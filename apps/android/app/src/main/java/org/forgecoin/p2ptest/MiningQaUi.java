package org.forgecoin.p2ptest;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.text.InputType;
import android.widget.*;

/** User-initiated loopback miner controls. No production endpoints. */
final class MiningQaUi {
    private MiningQaUi(){}
    private static EditText field(Activity a,LinearLayout form,String hint,int type) {
        EditText entry=new EditText(a);entry.setHint(hint);entry.setSingleLine(true);
        entry.setInputType(type);form.addView(entry);return entry;
    }
    static void ask(Activity a,int mode,int intensity) {
        if(!BuildConfig.DEBUG || !MiningService.runtimePresent(a))return;
        if(Build.VERSION.SDK_INT>=33 && a.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                !=PackageManager.PERMISSION_GRANTED) {
            a.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},801);
            Toast.makeText(a,"Allow the miner's stop notification, then start again",Toast.LENGTH_LONG).show();
            return;
        }
        LinearLayout form=new LinearLayout(a);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(24,12,24,12);
        EditText endpoint=field(a,form,"127.0.0.1:port",InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        EditText address=field(a,form,"Disposable standard FRG address",InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        EditText node=mode==0?null:field(a,form,"Loopback FAKECHAIN daemon port",InputType.TYPE_CLASS_NUMBER);
        AlertDialog dialog=new AlertDialog.Builder(a)
            .setTitle(mode==0?"Start isolated solo miner":"Start isolated pool miner")
            .setMessage("Use a disposable offline ForgeCoin chain through loopback. The service stops for heat, low battery, memory pressure or screen-off.")
            .setView(form).setNegativeButton("Cancel",null).setPositiveButton("Start",null).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            try {
                String url=endpoint.getText().toString().trim();
                int port=MiningConfiguration.loopbackPort(url);
                String wallet=address.getText().toString().trim();
                int nodePort=node==null?port:Integer.parseInt(node.getText().toString().trim());
                if(nodePort<1024 || nodePort>65535)throw new IllegalArgumentException("Invalid disposable node port");
                MiningConfiguration.buildCommand("miner",wallet,url,"android",mode,intensity,Runtime.getRuntime().availableProcessors());
                a.startForegroundService(new Intent(a,MiningService.class).setAction(MiningService.START)
                    .putExtra("endpoint",url).putExtra("address",wallet).putExtra("mode",mode)
                    .putExtra("worker","android").putExtra("intensity",intensity).putExtra("qaNodePort",nodePort));
                dialog.dismiss();
            } catch(IllegalArgumentException | IllegalStateException error) {
                Toast.makeText(a,"Check the loopback endpoint, node port and disposable FRG address",Toast.LENGTH_LONG).show();
            }
        }));
        dialog.show();
    }
}
