package org.forgecoin.p2ptest;

import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import org.json.JSONObject;

/** Identity gate for Android's disposable offline FAKECHAIN tests. */
final class FrgQaNode {
    static final String FROZEN_GENESIS="4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c";
    private FrgQaNode(){}
    static void requireIsolated(int port) throws Exception {
        JSONObject info=request(port,"/get_info",new JSONObject(),4000);
        String net=info.optString("nettype");
        if(!"OK".equals(info.optString("status")) || (!"fakechain".equals(net) && !"regtest".equals(net))
            || info.optLong("outgoing_connections_count",-1)!=0
            || info.optLong("incoming_connections_count",-1)!=0)
            throw new SecurityException("Expected an isolated, offline ForgeCoin FAKECHAIN daemon");
        JSONObject reply=rpc(port,"get_block_header_by_height",new JSONObject().put("height",0),4000);
        JSONObject header=reply.getJSONObject("result").getJSONObject("block_header");
        if(header.optLong("height",-1)!=0 || !FROZEN_GENESIS.equals(header.optString("hash")))
            throw new SecurityException("Daemon genesis identity does not match frozen ForgeCoin");
    }
    static JSONObject rpc(int port,String method,JSONObject params,int timeout) throws Exception {
        return request(port,"/json_rpc",new JSONObject().put("jsonrpc","2.0").put("id","isolated-android")
            .put("method",method).put("params",params),timeout);
    }
    private static JSONObject request(int port,String path,JSONObject data,int timeout) throws Exception {
        if(!BuildConfig.DEBUG || port<1024 || port>65535)
            throw new SecurityException("Only loopback Android debug QA is allowed");
        HttpURLConnection connection=(HttpURLConnection)new URL("http://127.0.0.1:"+port+path)
            .openConnection(Proxy.NO_PROXY);
        connection.setConnectTimeout(4000);connection.setReadTimeout(timeout);
        connection.setInstanceFollowRedirects(false);connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type","application/json");connection.setDoOutput(true);
        try {
            try(OutputStream out=connection.getOutputStream()){out.write(data.toString().getBytes(StandardCharsets.UTF_8));}
            if(connection.getResponseCode()!=200)throw new IOException("Local test RPC failed");
            try(InputStream input=connection.getInputStream();ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
                byte[] buf=new byte[4096];int read;
                while((read=input.read(buf))!=-1){
                    if(bytes.size()+read>65536)throw new IOException("Local RPC response exceeds limit");
                    bytes.write(buf,0,read);
                }
                return new JSONObject(bytes.toString("UTF-8"));
            }
        } finally {connection.disconnect();}
    }
}
