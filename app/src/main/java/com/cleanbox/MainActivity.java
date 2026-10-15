package com.cleanbox;
import android.app.Activity;
import android.os.*;
import android.widget.*;
import android.view.*;
import android.graphics.*;
import java.util.*;
import org.json.*;
import com.bumptech.glide.Glide;
public class MainActivity extends Activity {
  LinearLayout root;
  @Override protected void onCreate(Bundle s) {
    super.onCreate(s);
    ScrollView sv=new ScrollView(this);
    root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(16,16,16,16);
    sv.addView(root);
    setContentView(sv);
    TextView title=new TextView(this); title.setText("Cleanbox - For You"); title.setTextSize(20); title.setTypeface(null,Typeface.BOLD); root.addView(title);
    TextView sub=new TextView(this); sub.setText("Trending"); sub.setTextSize(16); sub.setPadding(0,16,0,8); root.addView(sub);
    new Thread(new Runnable(){
      public void run(){
        try{
          String json=CleanboxApi.trending();
          JSONObject obj=new JSONObject(json);
          JSONObject data=obj.optJSONObject("data");
          JSONArray results=data!=null?data.optJSONArray("results"):null;
          if(results==null){ final String js=json; runOnUiThread(new Runnable(){public void run(){TextView t=new TextView(MainActivity.this); t.setText("No data: "+js.substring(0,Math.min(500,js.length()))); root.addView(t);}}); return; }
          for(int i=0;i<Math.min(results.length(),10);i++){
            JSONObject topic=results.getJSONObject(i);
            JSONArray subjects=topic.optJSONArray("subjects");
            if(subjects==null) continue;
            for(int j=0;j<Math.min(subjects.length(),5);j++){
              final JSONObject sub2=subjects.getJSONObject(j);
              final String title2=sub2.optString("title","Untitled");
              final String cover=sub2.optJSONObject("cover")!=null?sub2.optJSONObject("cover").optString("url",""):"";
              runOnUiThread(new Runnable(){public void run(){ addCard(title2, cover); }});
            }
          }
        }catch(final Exception e){ runOnUiThread(new Runnable(){public void run(){TextView t=new TextView(MainActivity.this); t.setText("Error: "+e.getMessage()); root.addView(t);}}); }
      }
    }).start();
  }
  void addCard(String title, String cover){
    LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.HORIZONTAL); card.setPadding(8,8,8,8);
    ImageView iv=new ImageView(this); iv.setLayoutParams(new LinearLayout.LayoutParams(200,300)); iv.setScaleType(ImageView.ScaleType.CENTER_CROP);
    TextView tv=new TextView(this); tv.setText(title); tv.setPadding(16,0,0,0); tv.setTextSize(14);
    if(!cover.isEmpty()) Glide.with(this).load(cover).into(iv);
    card.addView(iv); card.addView(tv); root.addView(card);
  }
}
