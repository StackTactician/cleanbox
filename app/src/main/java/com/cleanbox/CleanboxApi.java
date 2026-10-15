  public static String search(String kw) throws Exception{
    String url="https://"+API_HOSTS[0]+BFF+"/subject-api/search/v2";
    String body="{\"keyword\":\""+kw+"\",\"page\":1,\"size\":10}";
    java.util.Map<String,String> h=new java.util.HashMap<>(); h.put("Accept","application/json"); h.put("Content-Type","application/json; charset=utf-8");
    String sig=sign("POST",url,body,h);
    okhttp3.Request r=new okhttp3.Request.Builder().url(url).post(okhttp3.RequestBody.create(body, okhttp3.MediaType.get("application/json; charset=utf-8")))
      .header("Accept","application/json").header("Content-Type","application/json; charset=utf-8").header("Authorization","Bearer "+TOKEN)
      .header("X-Client-Info","{\"packageName\":\"com.community.oneroom\",\"versionCode\":\"50020131\",\"versionName\":\"4.0.03.0922.03\",\"osVersion\":\"12\",\"phoneBrand\":\"Infinix\",\"phoneModel\":\"X6819\",\"deviceId\":\"528e87f3691ea51b\",\"channelId\":\"gp\"}")
      .header("x-tr-signature",sig).build();
    okhttp3.Response resp=client.newCall(r).execute();
    return resp.body().string();
  }
  public static String getPlayInfo(String sid) throws Exception{
    String url="https://"+API_HOSTS[0]+BFF+"/subject-api/play-info?subjectId="+sid;
    java.util.Map<String,String> h=new java.util.HashMap<>(); h.put("Accept","application/json"); h.put("Content-Type","application/json; charset=utf-8");
    String sig=sign("GET",url,null,h);
    okhttp3.Request r=new okhttp3.Request.Builder().url(url).get()
      .header("Accept","application/json").header("X-Client-Info","{\"packageName\":\"com.community.oneroom\",\"versionCode\":\"50020131\",\"versionName\":\"4.0.03.0922.03\",\"osVersion\":\"12\",\"phoneBrand\":\"Infinix\",\"phoneModel\":\"X6819\",\"deviceId\":\"528e87f3691ea51b\",\"channelId\":\"gp\"}")
      .header("Authorization","Bearer "+TOKEN).header("x-tr-signature",sig).build();
    okhttp3.Response resp=client.newCall(r).execute();
    return resp.body().string();
  }
}
