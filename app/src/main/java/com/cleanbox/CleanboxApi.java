package com.cleanbox;
import android.util.Base64;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.concurrent.TimeUnit;
import okhttp3.*;
public class CleanboxApi {
  static final String GATEWAY_SECRET="76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O";
  static final String TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjIwNjMzNTk2NzU2Njc0NzEzMTIsInV0cCI6MSwiZXhwIjoxNzk5ODQ4MDI5LCJpYXQiOjE3OTIwNzE3Mjl9.lIareVNYKuvsBLWX0NCEKFxeIuw0M2NepQNts9vlWFc";
  static final String[] API_HOSTS={"api4sg.aoneroom.com"};
  static final String BFF="/wefeed-mobile-bff";
  static OkHttpClient client = new OkHttpClient.Builder().proxy(java.net.Proxy.NO_PROXY).connectTimeout(10,TimeUnit.SECONDS).readTimeout(10,TimeUnit.SECONDS).build();
  static String hmac(String data) throws Exception{
    byte[] key=Base64.decode(GATEWAY_SECRET, Base64.DEFAULT);
    Mac mac=Mac.getInstance("HmacMD5");
    mac.init(new SecretKeySpec(key,"HmacMD5"));
    return Base64.encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
  }
  static String sign(String method, String url, String body, Map<String,String> headers) throws Exception{
    long ts=System.currentTimeMillis();
    String accept=headers.getOrDefault("Accept","");
    String ctype=headers.getOrDefault("Content-Type","");
    String clen=""; String md5="";
    if(body!=null){ clen=String.valueOf(body.getBytes(StandardCharsets.UTF_8).length); MessageDigest md=MessageDigest.getInstance("MD5"); md.update(body.getBytes(StandardCharsets.UTF_8),0,Math.min(body.length(),102400)); byte[] d=md.digest(); StringBuilder sb=new StringBuilder(); for(byte b:d) sb.append(String.format("%02x",b)); md5=sb.toString(); }
    String path=new URL(url).getPath();
    String q=new URL(url).getQuery(); String urlPart=path;
    if(q!=null){ String[] parts=q.split("&"); Arrays.sort(parts); StringBuilder sb=new StringBuilder(); for(String p:parts){ if(sb.length()>0) sb.append("&"); sb.append(URLDecoder.decode(p.split("=")[0],"utf-8")+"="+(p.contains("=")?URLDecoder.decode(p.split("=",2)[1],"utf-8"):"")); } urlPart=path+"?"+sb.toString(); }
    String s=method.toUpperCase()+"\n"+accept+"\n"+ctype+"\n"+clen+"\n"+ts+"\n"+md5+"\n"+urlPart;
    return ts+"|2|"+hmac(s);
  }
  public static String trending() throws Exception{
    String url="https://"+API_HOSTS[0]+BFF+"/subject-api/trending/v2";
    String body="{\"page\":1}";
    Map<String,String> h=new HashMap<>(); h.put("Accept","application/json"); h.put("Content-Type","application/json; charset=utf-8");
    String sig=sign("POST",url,body,h);
    Request r=new Request.Builder().url(url).post(RequestBody.create(body, MediaType.get("application/json; charset=utf-8")))
      .header("Accept","application/json").header("Content-Type","application/json; charset=utf-8").header("Authorization","Bearer "+TOKEN)
      .header("X-Client-Info","{\"packageName\":\"com.community.oneroom\",\"versionCode\":\"50020131\",\"versionName\":\"4.0.03.0922.03\",\"osVersion\":\"12\",\"phoneBrand\":\"Infinix\",\"phoneModel\":\"X6819\",\"deviceId\":\"528e87f3691ea51b\",\"channelId\":\"gp\"}")
      .header("x-tr-signature",sig).build();
    Response resp=client.newCall(r).execute();
    return resp.body().string();
  }
  public static String search(String kw) throws Exception{
    String url="https://"+API_HOSTS[0]+BFF+"/subject-api/search/v2";
    String body="{\"keyword\":\""+kw+"\",\"page\":1,\"size\":10}";
    Map<String,String> h=new HashMap<>(); h.put("Accept","application/json"); h.put("Content-Type","application/json; charset=utf-8");
    String sig=sign("POST",url,body,h);
    Request r=new Request.Builder().url(url).post(RequestBody.create(body, MediaType.get("application/json; charset=utf-8")))
      .header("Accept","application/json").header("Content-Type","application/json; charset=utf-8").header("Authorization","Bearer "+TOKEN)
      .header("X-Client-Info","{\"packageName\":\"com.community.oneroom\",\"versionCode\":\"50020131\",\"versionName\":\"4.0.03.0922.03\",\"osVersion\":\"12\",\"phoneBrand\":\"Infinix\",\"phoneModel\":\"X6819\",\"deviceId\":\"528e87f3691ea51b\",\"channelId\":\"gp\"}")
      .header("x-tr-signature",sig).build();
    Response resp=client.newCall(r).execute();
    return resp.body().string();
  }
  public static String getPlayInfo(String sid) throws Exception{
    String url="https://"+API_HOSTS[0]+BFF+"/subject-api/play-info?subjectId="+sid;
    Map<String,String> h=new HashMap<>(); h.put("Accept","application/json"); h.put("Content-Type","application/json; charset=utf-8");
    String sig=sign("GET",url,null,h);
    Request r=new Request.Builder().url(url).get()
      .header("Accept","application/json").header("X-Client-Info","{\"packageName\":\"com.community.oneroom\",\"versionCode\":\"50020131\",\"versionName\":\"4.0.03.0922.03\",\"osVersion\":\"12\",\"phoneBrand\":\"Infinix\",\"phoneModel\":\"X6819\",\"deviceId\":\"528e87f3691ea51b\",\"channelId\":\"gp\"}")
      .header("Authorization","Bearer "+TOKEN).header("x-tr-signature",sig).build();
    Response resp=client.newCall(r).execute();
    return resp.body().string();
  }
}
