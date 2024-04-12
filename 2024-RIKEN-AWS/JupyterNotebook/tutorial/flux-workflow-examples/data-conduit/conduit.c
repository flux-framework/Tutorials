#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdlib.h>
#include <errno.h>
#include <flux/core.h>

struct conduit_ctx {
    flux_t *h;
    struct sockaddr_un server_sockaddr;
    struct sockaddr_un client_sockaddr;
    int client_sock;
    bool connected;
    char *sockname;
    char *csockname;
    flux_msg_handler_t **handlers;
};

static void freectx (void *arg)
{
    struct conduit_ctx *ctx = (struct conduit_ctx *)arg;
    flux_msg_handler_delvec (ctx->handlers);
    free (ctx->sockname);
    free (ctx->csockname);
    if (ctx->connected)
        close (ctx->client_sock);
    free (ctx);
}

static struct conduit_ctx *getctx (flux_t *h)
{
    struct conduit_ctx *ctx = flux_aux_get (h, "conduit");
    if (!ctx) {
        char *user = getenv ("USER");
        ctx = malloc (sizeof (*ctx));
        ctx->connected = false;
        ctx->handlers = NULL;
        asprintf (&(ctx->sockname),  "/tmp/%s/mysock", user? user : "");
        asprintf (&(ctx->csockname),"/tmp/%s/mycsock", user? user : "");
        flux_aux_set (h, "conduit", ctx, freectx);
    }
    return ctx;
}

/* Foward the received JSON string to the datastore.py */
static int conduit_send (flux_t *h, const char *json_str)
{
    int rc = -1;
    int n = 0;
    struct conduit_ctx *ctx = getctx (h);

    n = (int) strlen (json_str);
    if ((rc = send (ctx->client_sock, (void *)&n, sizeof (n), 0)) == -1) {
        flux_log_error (h, "send error %s", __FUNCTION__);
        return rc;
    }
    if ((rc = send (ctx->client_sock, (void *)json_str, n, 0)) == -1) {
        flux_log_error (h, "send error %s", __FUNCTION__);
        return rc;
    }
    flux_log (h, LOG_INFO, "conduit_send succeed");
    return 0;
}

/* request callback called when conduit.put request is invoked */
static void conduit_put_request_cb (flux_t *h, flux_msg_handler_t *w,
                                    const flux_msg_t *msg, void *arg)
{
    int rc = -1;
    const char *topic = NULL;
    struct conduit_ctx *ctx = getctx (h);
    const char *data = NULL;

    flux_log (h, LOG_INFO, "conduit_put_request_cb:");
    if (ctx->connected == false) {
        flux_log (h, LOG_INFO, "conduit not connected");
        errno = ENOTCONN;
        goto done;
    }
    if (flux_request_unpack (msg, &topic, "{s:s}", "data", &data)) {
        flux_log_error (h, "%s", __FUNCTION__);
        goto done;
    }
    if (conduit_send (h, data) < 0)
        errno = EPROTO;
done:
    if (flux_respond (h, msg, errno, NULL) < 0)
        flux_log_error (h, "%s: flux_respond", __FUNCTION__);
}

/* open the Unix domain socket to talk to datastore.py */
static int conduit_open (flux_t *h)
{
    struct conduit_ctx *ctx = getctx (h);
    int rc = -1;
    int len = 0;
    char buf[256];
    memset(&(ctx->server_sockaddr), 0, sizeof(struct sockaddr_un));
    memset(&(ctx->client_sockaddr), 0, sizeof(struct sockaddr_un));

    if ((ctx->client_sock = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        flux_log (h, LOG_ERR, "SOCKET ERROR = %d\n", errno);
        goto done;
    }

    ctx->client_sockaddr.sun_family = AF_UNIX;
    strcpy(ctx->client_sockaddr.sun_path, ctx->csockname);
    len = sizeof(ctx->client_sockaddr);
    unlink (ctx->csockname);
    if ((rc = bind(ctx->client_sock,
              (struct sockaddr *)&ctx->client_sockaddr, len)) == -1) {
        flux_log (h, LOG_ERR, "BIND ERROR: %d\n", errno);
        close(ctx->client_sock);
        goto done;
    }
    flux_log (h, LOG_INFO, "Conduit client socket bound\n");

    ctx->server_sockaddr.sun_family = AF_UNIX;
    strcpy(ctx->server_sockaddr.sun_path, ctx->sockname);
    if ((rc = connect(ctx->client_sock,
                 (struct sockaddr *)&ctx->server_sockaddr, len)) == -1) {
        flux_log (h, LOG_ERR, "CONNECT ERROR = %d\n", errno);
        close(ctx->client_sock);
        goto done;
    }

    ctx->connected = true;
    flux_log (h, LOG_INFO, "Conduit socket connected\n");
    conduit_send (h, "{\"test\":101}");
    rc = 0;
done:
    return rc;
}


static struct flux_msg_handler_spec htab[] = {
    { FLUX_MSGTYPE_REQUEST, "conduit.put",  conduit_put_request_cb, 0 },
    FLUX_MSGHANDLER_TABLE_END
};

int mod_main (flux_t *h, int argc, char **argv)
{
    uint32_t rank = 0;
    struct conduit_ctx *ctx = getctx (h);

    if (conduit_open (h) < 0) {
        flux_log (ctx->h, LOG_ERR, "conduit_open failed");
        goto done;
    }
    if (flux_get_rank (h, &rank) < 0) {
        flux_log (ctx->h, LOG_ERR, "flux_get_rank failed");
        goto done;
    }

    /* Put the rank where this module is loaded into conduit key
     */
    flux_kvs_txn_t *txn = flux_kvs_txn_create ();
    flux_kvs_txn_pack (txn, 0, "conduit", "i", rank);
    flux_kvs_commit (h, 0, txn);
    flux_kvs_txn_destroy (txn);
    if (flux_msg_handler_addvec (h, htab, (void *)h,
                                 &ctx->handlers) < 0) {
        flux_log (ctx->h, LOG_ERR, "flux_msg_handler_addvec: %s", strerror (errno));
        goto done;
    }
    if (flux_reactor_run (flux_get_reactor (h), 0) < 0) {
        flux_log (h, LOG_ERR, "flux_reactor_run: %s", strerror (errno));
        goto done;
    }

done:
    return 0;
}

MOD_NAME ("conduit");

/*
 * vi:tabstop=4 shiftwidth=4 expandtab
 */
