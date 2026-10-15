package com.cleanbox;
import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import android.widget.TextView;
public class MainActivity extends AppCompatActivity {
  @Override protected void onCreate(Bundle s) {
    super.onCreate(s);
    TextView tv = new TextView(this);
    tv.setText("Cleanbox 1.0 - videos ready");
    tv.setTextSize(18);
    tv.setPadding(40,100,40,40);
    setContentView(tv);
  }
}
