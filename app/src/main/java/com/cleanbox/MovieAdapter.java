package com.cleanbox;
import android.view.*;
import android.widget.*;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import java.util.*;
import org.json.*;
public class MovieAdapter extends RecyclerView.Adapter<MovieAdapter.VH> {
  List<JSONObject> list=new ArrayList<>();
  OnClick click;
  interface OnClick{ void onClick(String sid); }
  MovieAdapter(OnClick c){click=c;}
  void setData(List<JSONObject> d){ list=d; notifyDataSetChanged(); }
  void addData(List<JSONObject> d){ int s=list.size(); list.addAll(d); notifyItemRangeInserted(s,d.size()); }
  public VH onCreateViewHolder(ViewGroup p,int t){ View v=LayoutInflater.from(p.getContext()).inflate(R.layout.item_movie,p,false); return new VH(v); }
  public void onBindViewHolder(VH h,int pos){ try{ JSONObject o=list.get(pos); h.title.setText(o.optString("title")); h.genre.setText(o.optString("genre")); String cover=o.optJSONObject("cover")!=null?o.optJSONObject("cover").optString("url"):""; if(!cover.isEmpty()) Glide.with(h.cover).load(cover).into(h.cover); h.btn.setOnClickListener(v-> click.onClick(o.optString("subjectId"))); h.itemView.setOnClickListener(v-> click.onClick(o.optString("subjectId"))); }catch(Exception e){} }
  public int getItemCount(){ return list.size(); }
  static class VH extends RecyclerView.ViewHolder{ TextView title,genre; ImageView cover; android.widget.Button btn; VH(View v){ super(v); title=v.findViewById(R.id.title); genre=v.findViewById(R.id.genre); cover=v.findViewById(R.id.cover); btn=v.findViewById(R.id.btn_play); } }
}
