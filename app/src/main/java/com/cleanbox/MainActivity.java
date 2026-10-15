package com.cleanbox;
import android.app.Activity;
import android.os.*;
import android.widget.*;
import android.view.*;
import android.graphics.*;
import android.content.Intent;
import java.util.*;
import org.json.*;
import com.bumptech.glide.Glide;
public class MainActivity extends Activity {
  LinearLayout root;
  EditText searchBox;
  @Override protected void onCreate(Bundle s) {
    super.onCreate(s);
    ScrollView sv=new ScrollView(this);
    root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(16,16,16,16);
    sv.addView(root);
    setContentView(sv);
    TextView title=new TextView(this); title.setText("Cleanbox - For You"); title.setTextSize(20); title.setTypeface(null,Typeface.BOLD); root.addView(title);
    LinearLayout searchRow=new LinearLayout(this); searchRow.setOrientation(LinearLayout.HORIZONTAL);
    searchBox=new EditText(this); searchBox.setHint("Search"); searchBox.setLayoutParams(new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
    Button searchBtn=new Button(this); searchBtn.setText("Go"); searchBtn.setOnClickListener(v-> doSearch(searchBox.getText().toString()));
    searchRow.addView(searchBox); searchRow.addView(searchBtn); root.addView(searchRow);
    TextView sub=new TextView(this); sub.setText("Trending"); sub.setTextSize(16); sub.setPadding(0,16,0,8); root.addView(sub);
    Button dlBtn=new Button(this); dlBtn.setText("Open Downloads"); dlBtn.setOnClickListener(v-> startActivity(new Intent(this, DownloadsActivity.class)));
    root.addView(dlBtn);
    loadTrending();
  }
  void doSearch(String kw){
    if(kw.isEmpty()) return;
    root.removeAllViews();
    TextView title=new TextView(this); title.setText("Search: "+kw); title.setTextSize(18); root.addView(title);
    new Thread(new Runnable(){ public void run(){
      try{
        String json=CleanboxApi.search(kw);
        JSONObject obj=new JSONObject(json);
        JSONObject data=obj.optJSONObject("data");
        JSONArray results=data!=null?data.optJSONArray("results"):null;
        if(results==null){ final String js=json; runOnUiThread(new Runnable(){public void run(){TextView t=new TextView(MainActivity.this); t.setText(js.substring(0,Math.min(500,js.length()))); root.addView(t);}}); return; }
        for(int i=0;i<Math.min(results.length(),10);i++){
          JSONObject topic=results.getJSONObject(i);
          JSONArray subjects=topic.optJSONArray("subjects");
          if(subjects==null) continue;
          for(int j=0;j<Math.min(subjects.length(),10);j++){
            final JSONObject sub2=subjects.getJSONObject(j);
            final String title2=sub2.optString("title","Untitled");
            final String cover=sub2.optJSONObject("cover")!=null?sub2.optJSONObject("cover").optString("url",""):"";
            final String sid=sub2.optString("subjectId","");
            runOnUiThread(new Runnable(){public void run(){ addCard(title2, cover, sid); }});
          }
        }
      }catch(final Exception e){ runOnUiThread(new Runnable(){public void run(){TextView t=new TextView(MainActivity.this); t.setText("Err "+e.getMessage()); root.addView(t);}}); }
    }}).start();
  }
  void loadTrending(){
    new Thread(new Runnable(){ public void run(){
      try{
        String json=CleanboxApi.trending();
        JSONObject obj=new JSONObject(json);
        JSONObject data=obj.optJSONObject("data");
        JSONArray results=data!=null?data.optJSONArray("results"):null;
        if(results==null) return;
        for(int i=0;i<Math.min(results.length(),10);i++){
          JSONObject topic=results.getJSONObject(i);
          JSONArray subjects=topic.optJSONArray("subjects");
          if(subjects==null) continue;
          for(int j=0;j<Math.min(subjects.length(),5);j++){
            final JSONObject sub2=subjects.getJSONObject(j);
            final String title2=sub2.optString("title","Untitled");
            final String cover=sub2.optJSONObject("cover")!=null?sub2.optJSONObject("cover").optString("url",""):"";
            final String sid=sub2.optString("subjectId","");
            runOnUiThread(new Runnable(){public void run(){ addCard(title2, cover, sid); }});
          }
        }
      }catch(Exception e){}
    }}).start();
  }
  void addCard(String title, String cover, final String sid){
    LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.HORIZONTAL); card.setPadding(8,8,8,8);
    ImageView iv=new ImageView(this); iv.setLayoutParams(new LinearLayout.LayoutParams(200,300)); iv.setScaleType(ImageView.ScaleType.CENTER_CROP);
    TextView tv=new TextView(this); tv.setText(title); tv.setPadding(16,0,0,0); tv.setTextSize(14);
    if(!cover.isEmpty()) Glide.with(this).load(cover).into(iv);
    card.addView(iv); card.addView(tv);
    card.setOnClickListener(new View.OnClickListener(){public void onClick(View v){ Intent i=new Intent(MainActivity.this, DetailActivity.class); i.putExtra("sid", sid); startActivity(i); }});
    root.addView(card);
  }
}
