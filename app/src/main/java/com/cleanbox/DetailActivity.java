package com.cleanbox;
import android.app.Activity;
import android.os.*;
import android.widget.*;
import android.content.Intent;
import android.net.Uri;
import org.json.*;
public class DetailActivity extends Activity {
  String sid;
  @Override protected void onCreate(Bundle s){
    super.onCreate(s);
    sid=getIntent().getStringExtra("sid");
    LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(16,16,16,16);
    android.widget.ScrollView sv=new android.widget.ScrollView(this); sv.addView(root);
    setContentView(sv);
    TextView t=new TextView(this); t.setText("Loading..."); root.addView(t);
    new Thread(new Runnable(){ public void run(){
      try{
        String json=CleanboxApi.getPlayInfo(sid);
        JSONObject obj=new JSONObject(json);
        JSONObject data=obj.optJSONObject("data");
        String playUrl="";
        if(data!=null){
          JSONArray streams=data.optJSONArray("streams");
          if(streams!=null && streams.length()>0) playUrl=streams.getJSONObject(streams.length()-1).optString("url","");
          if(playUrl.isEmpty()) playUrl=data.optString("playUrl","");
          if(playUrl.isEmpty()) playUrl=data.optString("url","");
        }
        final String url=playUrl;
        final String js=json;
        runOnUiThread(new Runnable(){ public void run(){
          if(url==null || url.isEmpty()){ t.setText("No playUrl: "+js.substring(0,Math.min(600,js.length()))); return; }
          t.setText("Ready");
          Button b=new Button(DetailActivity.this); b.setText("Stream"); b.setOnClickListener(new android.view.View.OnClickListener(){public void onClick(android.view.View v){ Intent i=new Intent(Intent.ACTION_VIEW); i.setDataAndType(Uri.parse(url), "video/*"); startActivity(i); }});
          Button d=new Button(DetailActivity.this); d.setText("Download"); d.setOnClickListener(new android.view.View.OnClickListener(){public void onClick(android.view.View v){
            new Thread(new Runnable(){ public void run(){
              try{
                java.io.File dir=getExternalFilesDir("downloads");
                if(dir!=null && !dir.exists()) dir.mkdirs();
                java.io.File out=new java.io.File(dir, sid+".mp4");
                okhttp3.Request req=new okhttp3.Request.Builder().url(url).build();
                okhttp3.Response resp=CleanboxApi.client.newCall(req).execute();
                java.io.InputStream is=resp.body().byteStream();
                java.io.FileOutputStream fos=new java.io.FileOutputStream(out);
                byte[] buf=new byte[8192]; int len; while((len=is.read(buf))!=-1) fos.write(buf,0,len);
                fos.close(); is.close();
                runOnUiThread(new Runnable(){public void run(){ Toast.makeText(DetailActivity.this,"Saved "+out.getName(),1).show(); }});
              }catch(final Exception e){ runOnUiThread(new Runnable(){public void run(){ Toast.makeText(DetailActivity.this,"Download err "+e.getMessage(),1).show(); }}); }
            }}).start();
          }});
          root.addView(b); root.addView(d);
        }});
      }catch(final Exception e){ runOnUiThread(new Runnable(){public void run(){ t.setText("Err "+e.getMessage()); }}); }
    }}).start();
  }
}
