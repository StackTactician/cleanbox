package com.cleanbox;
import android.os.*;
import android.content.Intent;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.*;
import com.google.android.material.tabs.TabLayout;
import org.json.*;
import java.util.*;
public class MainActivity extends AppCompatActivity {
  RecyclerView recycler; MovieAdapter adapter; TabLayout tabs; EditText searchBox;
  int page=1; boolean loading=false;
  String currentTab="For You"; String[] tabNames={"For You","Movies","Series","Trending"};
  @Override protected void onCreate(Bundle s){
    super.onCreate(s);
    setContentView(R.layout.activity_main);
    recycler=findViewById(R.id.recycler); tabs=findViewById(R.id.tab_layout); searchBox=findViewById(R.id.search_box);
    adapter=new MovieAdapter(sid-> { Intent i=new Intent(this, DetailActivity.class); i.putExtra("sid",sid); startActivity(i); });
    recycler.setLayoutManager(new LinearLayoutManager(this)); recycler.setAdapter(adapter);
    for(String n:tabNames) tabs.addTab(tabs.newTab().setText(n));
    tabs.addOnTabSelectedListener(new TabLayout.OnTabSelectedListener(){ public void onTabSelected(TabLayout.Tab t){ currentTab=t.getText().toString(); page=1; adapter.setData(new ArrayList<>()); load(); } public void onTabUnselected(TabLayout.Tab t){} public void onTabReselected(TabLayout.Tab t){} });
    findViewById(R.id.search_btn).setOnClickListener(v-> doSearch());
    findViewById(R.id.btn_downloads).setOnClickListener(v-> startActivity(new Intent(this, DownloadsActivity.class)));
    recycler.addOnScrollListener(new RecyclerView.OnScrollListener(){ public void onScrolled(RecyclerView r, int dx,int dy){ LinearLayoutManager lm=(LinearLayoutManager)r.getLayoutManager(); if(!loading && lm.findLastVisibleItemPosition()==adapter.getItemCount()-1){ page++; load(); } } });
    load();
  }
  void doSearch(){
    String kw=searchBox.getText().toString(); if(kw.isEmpty()) return;
    new Thread(()->{
      try{ String json=CleanboxApi.search(kw); List<JSONObject> out=new ArrayList<>(); JSONObject obj=new JSONObject(json); JSONArray res=obj.optJSONObject("data")!=null?obj.optJSONObject("data").optJSONArray("results"):null; if(res!=null) for(int i=0;i<res.length();i++){ JSONArray subs=res.getJSONObject(i).optJSONArray("subjects"); if(subs!=null) for(int j=0;j<subs.length();j++) out.add(subs.getJSONObject(j)); } runOnUiThread(()-> adapter.setData(out)); }catch(Exception e){ runOnUiThread(()-> Toast.makeText(this,"Search err "+e.getMessage(),1).show()); }
    }).start();
  }
  void load(){
    loading=true;
    new Thread(()->{
      try{
        String json;
        if(currentTab.equals("Trending")) json=CleanboxApi.trending();
        else json=CleanboxApi.trending();
        List<JSONObject> out=new ArrayList<>();
        JSONObject obj=new JSONObject(json);
        JSONArray res=obj.optJSONObject("data")!=null?obj.optJSONObject("data").optJSONArray("results"):null;
        if(res!=null) for(int i=0;i<res.length();i++){ JSONArray subs=res.getJSONObject(i).optJSONArray("subjects"); if(subs!=null) for(int j=0;j<subs.length();j++) out.add(subs.getJSONObject(j)); }
        runOnUiThread(()->{ if(page==1) adapter.setData(out); else adapter.addData(out); loading=false; });
      }catch(Exception e){ runOnUiThread(()->{ Toast.makeText(this,"Load err "+e.getMessage(),1).show(); loading=false; }); }
    }).start();
  }
}
