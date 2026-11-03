/*
Copyright (c) 2018, The Monero Project

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#define __STDC_FORMAT_MACROS
#include <inttypes.h>

#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>


#include <event2/event.h>
#include <event2/buffer.h>
#include <event2/http.h>

#include "log.h"
#include "pool.h"
#include "webui.h"
#include "frg_currency.h"

extern unsigned char webui_html[];
extern unsigned int webui_html_len;

static struct evhttp *webui_httpd;

static const char*
fetch_wa_cookie(struct evhttp_request *req)
{
    struct evkeyvalq *hdrs_in = evhttp_request_get_input_headers(req);
    const char *cookies = evhttp_find_header(hdrs_in, "Cookie");
    char *wa = NULL;

    if (cookies)
    {
        wa = strstr(cookies, "wa=");
        if (wa)
        {
            char *sc = strchr(wa, ';');
            if (sc)
                *sc = 0;
            wa += 3;
        }
    }
    return wa;
}

static void
send_json_workers(struct evhttp_request *req, void *arg)
{
    struct evbuffer *buf = evhttp_request_get_output_buffer(req);
    struct evkeyvalq *hdrs_out = NULL;
    char rig_list[0x40000] = {0};
    char *end = rig_list + sizeof(rig_list);
    const char *wa = fetch_wa_cookie(req);

    if (wa)
        worker_list(rig_list, end, wa);

    evbuffer_add_printf(buf, "[%s]", rig_list);
    hdrs_out = evhttp_request_get_output_headers(req);
    evhttp_add_header(hdrs_out, "Content-Type", "application/json");
    evhttp_send_reply(req, HTTP_OK, "OK", buf);
}

static void
send_json_stats(struct evhttp_request *req, void *arg)
{
    struct evbuffer *buf = evhttp_request_get_output_buffer(req);
    wui_context_t *context = (wui_context_t*) arg;
    struct evkeyvalq *hdrs_out = NULL;
    uint64_t ph = context->pool_stats->pool_hashrate;
    uint64_t nh = context->pool_stats->network_hashrate;
    uint64_t nd = context->pool_stats->network_difficulty;
    uint64_t height = context->pool_stats->network_height;
    uint64_t ltf = context->pool_stats->last_template_fetched;
    uint64_t lbf = context->pool_stats->last_block_found;
    uint32_t pbf = context->pool_stats->pool_blocks_found;
    uint64_t rh = context->pool_stats->round_hashes;
    unsigned ss = context->allow_self_select;
    double mh[6] = {0};
    uint64_t mb = 0;
    uint64_t wc = 0;
    const char *wa = fetch_wa_cookie(req);

    if (wa)
    {
        account_hr(mh, wa);
        wc = worker_count(wa);
        uint64_t balance = account_balance(wa);
        mb = balance;
    }

    evbuffer_add_printf(buf, "{"
            "\"pool_hashrate\":%"PRIu64","
            "\"round_hashes\":%"PRIu64","
            "\"network_hashrate\":%"PRIu64","
            "\"network_difficulty\":%"PRIu64","
            "\"network_height\":%"PRIu64","
            "\"last_template_fetched\":%"PRIu64","
            "\"last_block_found\":%"PRIu64","
            "\"pool_blocks_found\":%d,"
            "\"payment_threshold\":%g,"
            "\"pool_fee\":%g,"
            "\"pool_port\":%d,"
            "\"pool_ssl_port\":%d,"
            "\"allow_self_select\":%u,"
            "\"connected_miners\":%d,"
            "\"miner_hashrate\":%"PRIu64","
            "\"miner_hashrate_stats\":["
                    "%"PRIu64",%"PRIu64",%"PRIu64","
                    "%"PRIu64",%"PRIu64",%"PRIu64"],"
            "\"miner_balance\":%"PRIu64".%08"PRIu64","
            "\"worker_count\": %"PRIu64
            "}", ph, rh, nh, nd, height, ltf, lbf, pbf,
            context->payment_threshold, context->pool_fee,
            context->pool_port, context->pool_ssl_port,
            ss, context->pool_stats->connected_accounts,
            (uint64_t)mh[0],
            (uint64_t)mh[0], (uint64_t)mh[1], (uint64_t)mh[2],
            (uint64_t)mh[3], (uint64_t)mh[4], (uint64_t)mh[5],
            mb / FRG_ATOMIC_UNITS, mb % FRG_ATOMIC_UNITS, wc);
    hdrs_out = evhttp_request_get_output_headers(req);
    evhttp_add_header(hdrs_out, "Content-Type", "application/json");
    evhttp_send_reply(req, HTTP_OK, "OK", buf);
}

static void
process_request(struct evhttp_request *req, void *arg)
{
    const char *url = evhttp_request_get_uri(req);
    struct evbuffer *buf = NULL;
    struct evkeyvalq *hdrs_out = NULL;

    if (strstr(url, "/stats") != NULL)
    {
        send_json_stats(req, arg);
        return;
    }

    if (strstr(url, "/workers") != NULL)
    {
        send_json_workers(req, arg);
        return;
    }

    buf = evhttp_request_get_output_buffer(req);
    evbuffer_add(buf, webui_html, webui_html_len);
    hdrs_out = evhttp_request_get_output_headers(req);
    evhttp_add_header(hdrs_out, "Content-Type", "text/html");
    evhttp_send_reply(req, HTTP_OK, "OK", buf);
}

/* WebUI shares the pool event loop. This removes detached worker lifetime,
 * cross-thread libevent ownership and the SIGTERM/atexit deadlock window.
 * Both Stratum and HTTP continue to bind only the explicitly configured
 * local address in unreviewed research builds.
 */
int
start_web_ui(wui_context_t *context, struct event_base *base)
{
    if (!context || !base || webui_httpd)
        return -1;
    log_info("Starting Web UI on %s:%d", context->listen, context->port);
    webui_httpd = evhttp_new(base);
    if (!webui_httpd)
    {
        log_error("Failed to allocate native WebUI HTTP server");
        return -1;
    }
    if (!evhttp_bind_socket_with_handle(webui_httpd, context->listen,
                                        context->port))
    {
        log_error("Failed to bind WebUI to %s:%d", context->listen, context->port);
        evhttp_free(webui_httpd);
        webui_httpd = NULL;
        return -1;
    }
    evhttp_set_gencb(webui_httpd, process_request, context);
    return 0;
}

void
stop_web_ui(void)
{
    /* Called only after the shared pool dispatcher has returned.
     * evhttp_free closes HTTP listeners; the pool owns event_base_free.
     */
    if (webui_httpd)
    {
        evhttp_free(webui_httpd);
        webui_httpd = NULL;
    }
}

