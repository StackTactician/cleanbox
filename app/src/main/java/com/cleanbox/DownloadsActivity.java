package com.cleanbox;
import android.app.Activity;
import android.os.*;
import android.widget.*;
import java.io.*;
public class DownloadsActivity extends Activity {
  @Override protected void onCreate(Bundle s){
    super.onCreate(s);
    LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(16,16,16,16);
    ScrollView sv=new ScrollView(this); sv.addView(root);
    setContentView(sv);
    TextView t=new TextView(this); t.setText("Downloads"); t.setTextSize(18); root.addView(t);
    File dir=getExternalFilesDir("downloads");
    if(dir==null || !dir.exists() || dir.listFiles()==null || dir.listFiles().length==0){
      TextView e=new TextView(this); e.setText("No downloads yet"); root.addView(e); return;
    }
    for(File f: dir.listFiles()){
      TextView tv=new TextView(this); tv.setText(f.getName()+" "+(f.length()/1024/1024)+"MB"); tv.setPadding(8,8,8,8); root.addView(tv);
    }
  }
}
