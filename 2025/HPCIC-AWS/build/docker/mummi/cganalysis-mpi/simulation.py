#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (c) 2021, Lawrence Livermore National Security, LLC. All rights
# reserved. LLNL-CODE-827655. This work was produced at the Lawrence Livermore
# National Laboratory (LLNL) under contract no. DE-AC52-07NA27344 (Contract 44)
# between the U.S. Department of Energy (DOE) and Lawrence Livermore National
# Security, LLC (LLNS) for the operation of LLNL.  See license for disclaimers,
# notice of U.S. Government Rights and license terms and conditions.
# -----------------------------------------------------------------------------

from abc import ABC, abstractmethod, abstractproperty
import os
from shutil import copy2, which
from time import sleep
from logging import getLogger
import shlex

from typing import List
from mummi_core.utils import Naming
from mummi_ras.parsers.cg import CGParser

LOGGER = getLogger(__name__)

import flux
import flux.job
from flux.job import JobspecV1

handle = flux.Flux()


class SuccessCriteria(ABC):
    @abstractmethod
    def __init__(self, sim_dir, **kwargs):
        pass

    @abstractmethod
    def __bool__(self):
        pass


def is_running(flux_future):
    """
    Simple function to determine if job is running.
    """
    return job_info(flux_future).returncode == ""


def is_successed(flux_future):
    """
    Simple function to determine if job is running.
    """
    return job_info(flux_future).returncode in [0, "0"]


def stream_job_output(flux_future):
    """
    Given a jobid, stream the output
    """
    try:
        for line in flux.job.event_watch(handle, flux_future.get_id(), "guest.output"):
            if "data" in line.context:
                yield line.context["data"]
    except Exception:
        pass


def job_info(flux_future):
    """
    Simple function to determine if job is running.
    """
    payload = {"id": flux_future.get_id(), "attrs": ["all"]}
    rpc = flux.job.list.JobListIdRPC(handle, "job-list.list-id", payload)
    return rpc.get_jobinfo()


def submit_flux_job(command, num_tasks=1, num_nodes=1, cwd=None):
    """
    Submit a Flux job. This should throw up if it fails.
    """
    # Create the jobspec with nodes, tasks, etc.
    jobspec = JobspecV1.from_command(
        command=command,
        num_tasks=num_tasks,
        num_nodes=num_nodes,
    )

    # You can customize the job specification further
    cwd = cwd or os.getcwd()
    jobspec.cwd = cwd
    jobspec.environment = dict(os.environ)
    jobspec.stdout = os.path.join(cwd, "cganalysis.log")
    flux_future = flux.job.submit_async(handle, jobspec)
    print(
        f"cganalysis job successfully submitted on {num_nodes} nodes with {num_tasks} tasks with ID: {flux_future.get_id()}"
    )
    return flux_future


class Simulation(ABC):
    def __init__(
        self,
        sim_name: str,
        input_dir: str,
        out_dir: str,
        remote_dir: str,
        bin_path: str,
        cg: CGParser,
        r_limit: int = 2,
    ):

        # Back end process for simulation management
        self.sim_name = sim_name
        self.restart_limit = r_limit  # Limit to number of restarts
        self._setup = False  # Is the simulation setup?
        self._future = None  # Initialize the flux future to None
        self._success = {}  # Label success criteria
        self.cg = cg  # CGParser object that contains MDA universe

        # Lazy way to set nodes :)
        self.nodes = int(os.environ.get("CG_NODES", "1") or "1")

        # Pathing for inputs and outputs
        self.sim_dir = os.path.abspath(out_dir)  # Path for simulation run
        self.remote_dir = os.path.abspath(
            remote_dir
        )  # Path for remote simulation run (Lustre or GPFS)
        self.input_dir = os.path.abspath(input_dir)  # Path containing inputs
        self.bin_path = which(bin_path)  # Path to simulation code
        if not self.bin_path:
            self.bin_path = os.path.abspath(bin_path)
            LOGGER.error(f"{bin_path} was not in PATH: abspath={self.bin_path}")

    def add_success_criteria(self, criteria):
        if not isinstance(SuccessCriteria, criteria):
            raise TypeError(
                "A simulation success criteria must be of type "
                "'SuccessCriteria'. Received an object of type "
                f"'{type(criteria)}'."
            )

        criteria_name = criteria.__class__.__name__
        if criteria_name in self._success:
            raise ValueError(
                f"A SuccessCriteria of type '{criteria_name}' has already "
                "been added."
            )

        self._success[criteria_name] = criteria

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def setup_restart(self):
        pass

    @abstractmethod
    def equilibrate(self):
        pass

    def run(self):
        if not self._setup:
            raise Exception("Simulation not setup prior to running. Aborting.")

        LOGGER.info(f"Starting {self.bin_path}....")

        # Assemble command for flux
        cmd = f"{self.bin_path} mdrun -rcon 0.4 -cpi -pin off -maxh 0.1"
        LOGGER.info("cmd =       %s", cmd)
        LOGGER.info("os.pwd =    %s", os.getcwd())
        LOGGER.info("simdir =    %s", self.sim_dir)

        # Original command
        #   /tmp/workdir/gmx mdrun -cpi -ntmpi 1 -ntomp 64 -pin off -maxh 0.1
        # Flux potential command.
        #   flux run -N1 -n 64 gmx_mpi mdrun -rcon 0.4 -cpi -pin off -maxh 0.1
        # This is mpirun - we don't need -ntomp 1  if we run with flux that has MPI
        #   -ntomp is the number of threads per rank
        #   -ntmpi is the number of ranks
        #   mpirun --allow-run-as-root -np 64 gmx_mpi mdrun -rcon 0.4 -cpi -pin off -maxh 0.1
        os.putenv("OMP_NUM_THREADS", "")
        if "OMP_NUM_THREADS" in os.environ:
            del os.environ["OMP_NUM_THREADS"]
        print(cmd)

        # Submit to flux async
        command = shlex.split(
            f"{self.bin_path} mdrun -rcon 0.4 -cpi -pin off -maxh 0.1"
        )

        # Defaults to one core per task.
        self._future = submit_flux_job(
            command,
            num_tasks=self.ncores * self.nodes,
            num_nodes=self.nodes,
            cwd=self.sim_dir,
        )

        sleep(5)
        LOGGER.info("Process Running? %s", is_running(self._future))

        cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "UNSET")
        rocm_visible_devices = os.environ.get("ROCR_VISIBLE_DEVICES", "UNSET")
        LOGGER.info(f"CUDA_VISIBLE_DEVICES={cuda_visible_devices}")
        LOGGER.info(f"ROCR_VISIBLE_DEVICES={rocm_visible_devices}")

        self.check()

    def __bool__(self):
        return bool(self._future is not None)

    def stop(self):
        LOGGER.info(f"Stopping simulation {self.sim_name}")

        if self._future is not None:
            # We could also send a signal, but this should work
            flux.job.cancel(handle, self._future.get_id(), "cganalysis stop request")
            with open(os.path.join(self.sim_dir, "mdrun.log"), "w") as fd:
                for line in stream_job_output(self._future):
                    print(line)
                    fd.write(line)

    @property
    def running(self):
        return self._future is not None and is_running(self._future)

    @property
    def successful(self):
        print("Checking for job success...")
        # Write log here as a hack
        if self._future is not None:
            with open(os.path.join(self.sim_dir, "mdrun.log"), "w") as fd:
                for line in stream_job_output(self._future):
                    print(line)
                    fd.write(line)

    def check(self):
        if self._future is not None and is_running(self._future):
            print("Job is running.")

    @abstractmethod
    def get_frame_folder(self) -> str:
        """Return the folder name on disk for the current frame counter."""
        pass

    @abstractmethod
    def get_sim_file(self) -> str:
        """Return the simulation name corresponding to the frame."""
        pass

    @abstractmethod
    def get_new_frames(self, counter_incr: int = None) -> List[int]:
        """
        Return the new frames available for processing as a list of frame ID.

        counter_incr: represents the increment between each frame read
        """
        pass

    @abstractmethod
    def update_frame(self, fname: str = None) -> None:
        """
        Return the new frames available for processing as a list of frame ID.

        fname: The frame Name/ID or trajectory file
        """
        pass


class ddcMDLengthCriteria(SuccessCriteria):
    def __init__(self, sim_dir, length=1.0e9, snapshot_freq=25000, dt=20):
        self.length = length
        self.snap_freq = snapshot_freq
        self.dt = dt
        self.sim_dir = sim_dir

    def get_snapshot(self):
        return f"snapshot.{int(self.length / self.dt):012d}"

    def __bool__(self):
        snapshot_dir = os.path.join(self.sim_dir, self.get_snapshot(), "subset#000000")
        return os.path.exists(snapshot_dir)


class ddcMD(Simulation):
    def initialize(self):
        # If we've already run, we shouldn't setup again.
        if self._future is not None:
            return

        # Create the simulation workspace.
        if not os.path.exists(self.sim_dir):
            os.mkdir(self.sim_dir)

        # Copy input files to the directory.
        # This path will usually be the createsim directory as it is
        # supposed to
        # inputs = [
        #     'ConsAtom.data', 'martini.data', 'molecule.data', 'object.data',
        #     'restraint.data', 'topol.tpr', 'lipids-water-eq4.gro',
        #     'lipids-water-eq4hvr.gro', 'POPX_Martini_v2.0_lipid.itp',
        #     'resItpList'
        # ]
        inputs = []

        try:
            for in_file in inputs:
                src = os.path.join(self.input_dir)
                copy2(src, self.sim_dir)
        except Exception as err:
            LOGGER.error(err.message)
            raise err

        # TODO: Commented for now, but will be added in the future.
        # Set up restart file (copy over and symlink)
        # restart_path = os.path.join(self.input_dir, self.restart_snap)
        # copytree(restart_path, self.sim_dir)
        # src = os.path.join(self.sim_dir, self.restart_snap, "restart")
        # dst = os.path.join(self.sim_dir, "restart")
        # os.symlink(src, dst)

        self._setup = True

    @property
    def command(self):
        return f"{self.bin_path} -o object.data molecule0.data martini0.data constraint0.data >> ddcmd.out"

    def equilibrate(self):
        pass

    def setup_restart(self):
        pass

    @property
    def successful(self):
        success = ddcMDLengthCriteria(self.sim_dir)
        return bool(success)

    def get_frame_folder(self) -> str:
        return "snapshot.{:012d}".format(self.fcounter)

    def get_sim_file(self) -> str:
        fname = f"{self.get_frame_folder()}/subset#000000"
        if len(self.extension) > 0:
            fname = fname + f".{self.extension}"
        return os.path.join(self.path, fname)

    def get_new_frames(self, counter_incr: int = None) -> List[int]:
        if not self.running:
            return []
        cFrameList = []
        while True:
            fnameTraj = self.get_sim_file()
            LOGGER.info(f"Checking for frame {fnameTraj}")
            if os.path.isfile(fnameTraj):  # file not found try later
                # Note from vsoch: this has to be a bug (cfcounter not defined here)
                cFrameList.append(cfcounter)
                self.cfcounter = self.cfcounter + counter_incr
            else:
                break
        return cFrameList

    def update_frame(self, fname: str = None):
        # This replaces this old cordinates with the new
        self.cg.syst.load_new(fname, format="DDCMD")


class GROMACS(Simulation):
    def __init__(
        self,
        iointerface,
        xtc_file: str,
        ncores: int,
        stopsimtime: int,
        fcounter: int = 0,
        extension: str = "gro",
        runtime_hours: int = -1,
        no_gpu: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sim_length = 0  # Simulated time in nanosecond
        self.fcounter = fcounter  # Frame counter
        self.ncores = ncores  # Number of cores dedicated to the simulation
        self.iointerface = iointerface  # MuMMI I/O interface
        self.extension = extension  # Extension of the file format
        self.xtc_file = xtc_file  # XTC file
        self.runtime_hours = float(runtime_hours)  # Runtime limit for the simulation
        self.stopsimtime = (
            stopsimtime  # Stop criteria in ns (we stop simulation after that)
        )
        self.no_gpu = no_gpu

    def initialize(self):
        # If we've already run, we shouldn't setup again.
        if self._future is not None:
            return
        # os.makedirs(self.sim_dir, exist_ok=True) # creatsims will always have created the dir
        self._setup = True
        self.flag_set = False  # Success flag

    def equilibrate(self):
        pass

    def setup_restart(self):
        pass

    @property
    def successful(self):
        sim_success_flag = self.sim_length >= self.stopsimtime
        if sim_success_flag and not self.flag_set:
            success_flag, _, stop_flag = Naming.status_flags("cg")
            if not self.iointerface.test_signal(self.remote_dir, stop_flag):
                self.iointerface.send_signal(self.remote_dir, stop_flag)
                LOGGER.info(
                    f"Setting stop flag for {self.remote_dir} (lenght {self.sim_length} ns)"
                )
                self.flag_set = True
        return sim_success_flag

    def get_frame_folder(self, fcounter) -> str:
        # No Folder in GROMACS
        return ""

    def get_sim_file(self) -> str:
        return f"{self.sim_name}_cg000_f{self.fcounter}.{self.extension}"

    def update_frame(self, fname: str = None):
        """
        Update the fame number in place
        """
        if not fname:
            fname = self.xtc_file
        # We test that the frame is not empty otherwise MDA crashes
        # GROMACS case, we reload the entire XTC only if the XTC has been modified since last time
        if (
            os.stat(fname).st_size > 0
            and os.stat(fname).st_mtime > self.cg.fnametraj_ts
        ):
            self.cg.syst.load_new(fname)
            self.cg.fnametraj_ts = os.stat(fname).st_mtime
        else:
            LOGGER.debug(
                f"We do not load {fname} as it did not get modified since last time"
            )

    def get_new_frames(self, counter_incr: int = None) -> List[int]:
        if not self.running:
            return []
        cFrameList = []

        prev_nframes = self.cg.syst.trajectory.n_frames
        # This re-load the entire xtc file (in case of GROMACS) but only if the xtc has been modified (i.e, GROMACS added a frame)
        self.update_frame()
        self.sim_length = (
            self.cg.syst.trajectory[-1].time / 1000
        )  # We set the simulation lenght in nanoseconds
        LOGGER.debug(
            f"{self.cg.syst.trajectory.n_frames} frames in trajectory ({self.cg.syst.trajectory.n_frames - prev_nframes} new frames since last time we checked)"
        )
        if self.fcounter < self.cg.syst.trajectory.n_frames:
            cFrameList = cFrameList + list(
                range(self.fcounter, self.cg.syst.trajectory.n_frames)
            )
            LOGGER.info(
                f"Getting all frame numbers in trajectory from {self.fcounter} to {self.cg.syst.trajectory.n_frames - 1}."
            )
            self.fcounter = self.cg.syst.trajectory.n_frames
            LOGGER.debug(f"Setting cfcounter to {self.fcounter}")
        return cFrameList


class GROMACS_PARTS(Simulation):
    # Same class as GROMACS except reads/writes output in parts
    def __init__(
        self,
        iointerface,
        xtc_file: str,
        ncores: int,
        stopsimtime: int,
        fcounter: int = 0,
        extension: str = "xtc",
        runtime_hours: int = -1,
        no_gpu: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.sim_length = 0  # Simulated time in nanosecond
        self.samplerate = (
            25000  # frame step interval save rate (20fs step rate this is 0.5 ns)
        )
        self.bundlingsize = 10  # How many frames are in each .xtc bundled
        self.fcounter = int(
            fcounter / self.samplerate
        )  # Frame counter - this is the frame we are at now
        #  - fcounter * samplerate * 0.02 ps = time
        #  - fcounter * samplerate = step number
        self.ncores = ncores  # Number of cores dedicated to the simulation
        self.no_gpu = no_gpu  # Remove GPU requirement (dev/testing only)
        self.iointerface = iointerface  # MuMMI I/O interface
        self.extension = extension  # Extension of the file format
        self.xtc_file = xtc_file  # XTC file - Note this variable is not used for now @TODO set so we use in parts
        self.runtime_hours = float(runtime_hours)  # Runtime limit for the simulation
        self.stopsimtime = (
            stopsimtime  # Stop criteria in ns (we stop simulation after that)
        )

    def initialize(self):
        # If we've already run, we shouldn't setup again.
        if self._future is not None:
            return
        # os.makedirs(self.sim_dir, exist_ok=True) # creatsims will always have created the dir
        self._setup = True
        self.flag_set = False  # Success flag

    def equilibrate(self):
        pass

    def setup_restart(self):
        pass

    @property
    def successful(self):
        sim_success_flag = self.sim_length >= self.stopsimtime
        if sim_success_flag and not self.flag_set:
            success_flag, _, stop_flag = Naming.status_flags("cg")
            if not self.iointerface.test_signal(self.remote_dir, stop_flag):
                self.iointerface.send_signal(self.remote_dir, stop_flag)
                LOGGER.info(
                    f"Setting stop flag for {self.remote_dir} (lenght {self.sim_length} ns)"
                )
                self.flag_set = True
            else:
                LOGGER.info(
                    f"Flag already set in {self.remote_dir} (lenght {self.sim_length} ns)"
                )
        return sim_success_flag

    def get_frame_folder(self, fcounter) -> str:
        # No Folder in GROMACS
        return ""

    def get_sim_file(self) -> str:
        return get_sim_file(self.fcounter)

    def get_part_frame_num(self, cFrameNum) -> int:
        # @TODO check if correct .xtc selected/loaded

        # convert to in .xtc 0-9 index
        # @TODO this is now hardcoded in cganalysis progress frame (as sim object was not there)
        return 0

    def get_sim_file(self, fcounter):
        # example of name traj_comp.step000002750000.xtc
        intCount = int(fcounter)
        return f"traj_comp.step{intCount:012d}.{self.extension}"

    def update_frame(self, fname: str = None):
        """
        Update the fame number in place
        """
        if not fname:
            fname = self.get_sim_file()

        # GROMACS_PARTS case open if not the same
        LOGGER.info(f"Open new .xtc {fname}")
        self.cg.syst.load_new(fname)

        # Something GROMACS restart and append in the current files which has already frames resulting into extra frames
        if self.cg.syst.trajectory.n_frames != self.bundlingsize:
            LOGGER.warning(
                f"{fname} has more/less frames {self.cg.syst.trajectory.n_frames} than expected ({self.bundlingsize})"
            )
            # Remove duplicate frames (if keep_original True we keep the orig XTC renamed traj_comp.step00000XXX.xtc.orig)
            self.cg.remove_duplicate_frame(fname, keep_original=True)
            # reload trajectory w/ duplicated frames (hopefully)
            self.cg.syst.load_new(fname)
            if self.cg.syst.trajectory.n_frames != self.bundlingsize:
                LOGGER.error(
                    f"Remove duplicate for {fname} did not work (#frames in traj: {self.cg.syst.trajectory.n_frames})"
                )

    def get_new_frames(self, counter_incr: int = None) -> List[int]:
        # @TODO need to update this for noninteracting drugs
        if not self.running:
            return []

        cFrameList = []
        step_open = 0
        if self.cg.fnametraj_ts == -1:
            # fnametraj_ts is -1 at start so no open .xtc
            # now use fcounter to find where to start
            # @WARNING assumign inital fcouner is always right index into file
            step_open = self.fcounter * self.samplerate
        else:
            # fnametraj_ts is the step count for the currently open .xtc files
            # we want to open the next one
            step_open = self.cg.fnametraj_ts + (self.samplerate * self.bundlingsize)

        step_next = step_open + (self.samplerate * self.bundlingsize)

        file_open = self.get_sim_file(step_open)
        file_next = self.get_sim_file(step_next)

        LOGGER.debug(
            f"Want to open {file_open} if {file_next} is present {self.cg.fnametraj_ts},{self.fcounter}"
        )

        # @WARNING this is relative path, works if like default cganalysis runs in the sim folder
        if os.path.isfile(file_next):
            # If next xtc parts exist that means that current is done all x10 frame readdy and we process
            self.update_frame(fname=file_open)
            # there shoudl be 10 frames per part
            cFrameList = list(
                range(
                    int(self.fcounter),
                    self.cg.syst.trajectory.n_frames + int(self.fcounter),
                )
            )
            self.cg.fnametraj_ts = step_open
            self.fcounter += self.cg.syst.trajectory.n_frames
            # We update the simulation length to know when to stop
            self.sim_length = (
                self.cg.syst.trajectory[-1].time / 1000
            )  # We set the simulation lenght in nanoseconds

        return cFrameList


class NoSimulation(Simulation):
    def __init__(self, xtc_file: str, **kwargs):
        super().__init__(**kwargs)
        self.xtc_file = xtc_file  # XTC file

    def initialize(self):
        self._setup = True

    def equilibrate(self):
        pass

    def setup_restart(self):
        pass

    @property
    def successful(self):
        return False

    def update_frame(self, fname: str = None):
        """
        Update the fame number in place (by default it's GROMACS)
        """
        if not fname:
            fname = self.xtc_file
        self.syst.load_new(fname)
