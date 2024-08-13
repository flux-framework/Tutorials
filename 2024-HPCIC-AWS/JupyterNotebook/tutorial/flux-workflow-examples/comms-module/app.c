#include <stdlib.h>
#include <errno.h>
#include <flux/core.h>

#if !defined (IO_SERVICE) && !defined (COMP_SERVICE)
# error "Either IO_SERVICE or COMP_SERVICE macro is needed"
#endif

struct app_ctx {
    flux_t *h;
    int count;
    flux_msg_handler_t **handlers;
};

static void freectx (void *arg)
{
    struct app_ctx *ctx = (struct app_ctx *)arg;
    flux_msg_handler_delvec (ctx->handlers);
    free (ctx);
}

static struct app_ctx *getctx (flux_t *h)
{
#if IO_SERVICE
    struct app_ctx *ctx = flux_aux_get (h, "ioapp");
#elif COMP_SERVICE
    struct app_ctx *ctx = flux_aux_get (h, "capp");
#endif
    if (!ctx) {
        ctx = malloc (sizeof (*ctx));
        ctx->count = 0;
        ctx->handlers = NULL;
#if IO_SERVICE
        flux_aux_set (h, "ioapp", ctx, freectx);
#elif COMP_SERVICE
        flux_aux_set (h, "capp", ctx, freectx);
#endif
    }
    return ctx;
}

#if IO_SERVICE
static void io_request_cb (flux_t *h, flux_msg_handler_t *w,
                           const flux_msg_t *msg, void *arg)
{
    const char *topic = NULL;
    struct app_ctx *ctx = getctx (h);
    int data = 0;

    if (flux_request_unpack (msg, &topic, "{s:i}", "data", &data))
        goto error;
    ctx->count++;
    if (flux_respond_pack (h, msg, "{s:i}", "count", ctx->count) < 0)
        flux_log_error (h, "%s", __FUNCTION__);
    flux_log (h, LOG_DEBUG, "count: %d", ctx->count);
    return;

error:
    flux_log_error (h, "%s", __FUNCTION__);
    if (flux_respond (h, msg, NULL) < 0)
        flux_log_error (h, "%s: flux_respond", __FUNCTION__);
}
#endif

#if COMP_SERVICE
static void comp_request_cb (flux_t *h, flux_msg_handler_t *w,
                             const flux_msg_t *msg, void *arg)
{
    const char *topic = NULL;
    struct app_ctx *ctx = getctx (h);
    int data = 0;

    flux_log (h, LOG_INFO, "comp_request_cb:");
    if (flux_request_unpack (msg, &topic, "{s:i}", "data", &data))
        goto error;

    ctx->count++;
    if (flux_respond_pack (h, msg, "{s:i}", "count", ctx->count) < 0)
        flux_log_error (h, "%s", __FUNCTION__);
    return;

error:
    flux_log_error (h, "%s", __FUNCTION__);
    if (flux_respond (h, msg, NULL) < 0)
        flux_log_error (h, "%s: flux_respond", __FUNCTION__);
}
#endif

static struct flux_msg_handler_spec htab[] = {
#if IO_SERVICE
    { FLUX_MSGTYPE_REQUEST, "ioapp.io",  io_request_cb, 0 },
#endif

#if COMP_SERVICE
    { FLUX_MSGTYPE_REQUEST, "capp.comp",  comp_request_cb, 0 },
#endif

    FLUX_MSGHANDLER_TABLE_END
};


int mod_main (flux_t *h, int argc, char **argv)
{

    struct app_ctx *ctx = getctx (h);
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

#if IO_SERVICE
MOD_NAME ("ioapp");
#elif COMP_SERVICE
MOD_NAME ("capp");
#endif

/*
 * vi:tabstop=4 shiftwidth=4 expandtab
 */
