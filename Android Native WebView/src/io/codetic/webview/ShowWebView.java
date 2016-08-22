package io.codetic.webview;

import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Context;
import android.webkit.WebView;
import android.webkit.WebViewClient;


public class ShowWebView extends Activity {

	   private boolean haveNetworkConnection() {
		      boolean haveConnectedWifi = false;
		      boolean haveConnectedMobile = false;

		      ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
		      NetworkInfo[] netInfo = cm.getAllNetworkInfo();

		  for (NetworkInfo ni : netInfo) {
		     if (ni.getTypeName().equalsIgnoreCase("WIFI"))
		        if (ni.isConnected())
		            haveConnectedWifi = true;
		    if (ni.getTypeName().equalsIgnoreCase("MOBILE"))
		        if (ni.isConnected())
		            haveConnectedMobile = true;
		}
		return haveConnectedWifi || haveConnectedMobile;
		}
	 
    //private Button button;
    private WebView webView;
    public void onCreate(Bundle savedInstanceState) {
         
        super.onCreate(savedInstanceState);
        //This will not show title bar 
        this.requestWindowFeature(Window.FEATURE_NO_TITLE);

        setContentView(R.layout.show_web_view);
         
        //Get webview
        webView = (WebView) findViewById(R.id.webView1);
        if(haveNetworkConnection()){
        startWebView("http://fingerstore.com.br/");
        } else {
            webView.loadUrl("file:///android_asset/error.html");
           }
    }
     
    private void startWebView(String url) {
         
        //Create new webview Client to show progress dialog
        //When opening a url or click on link
         
        webView.setWebViewClient(new WebViewClient() {     
            ProgressDialog progressDialog;
          
            //If you will not use this method url links are opeen in new brower not in webview
            public boolean shouldOverrideUrlLoading(WebView view, String url) {             
                view.loadUrl(url);
                return true;
            }
            //If url has "tel:245678", on clicking the number it will directly call to inbuilt calling feature of phone  
            public boolean shouldOverrideUrlLoading(WebView view, String url){
			    	
		 	    	if(url.startsWith("tel:")){
			    		Intent intent = new Intent(Intent.ACTION_DIAL, Uri.parse(url));
			    		startActivity(intent);
			    	} else {
			    		
			    		view.loadUrl(url);
			    		
			    	}
        }
        
            //Show loader on url load
            public void onLoadResource (WebView view, String url) {
                if (progressDialog == null) {
                    // in standard case YourActivity.this
                    progressDialog = new ProgressDialog(ShowWebView.this);
                    progressDialog.setMessage("Loading...");
                    progressDialog.show();
                }
            }
            public void onPageFinished(WebView view, String url) {
                try{
                if (progressDialog.isShowing()) {
                    progressDialog.dismiss();
                    progressDialog = null;
                }
                }catch(Exception exception){
                    exception.printStackTrace();
                }
            }
             
        });
          
         // Javascript inabled on webview 
        webView.getSettings().setJavaScriptEnabled(true);
         
        // Other webview options
        /*
        webView.getSettings().setLoadWithOverviewMode(true);
        webView.getSettings().setUseWideViewPort(true);
        webView.setScrollBarStyle(WebView.SCROLLBARS_OUTSIDE_OVERLAY);
        webView.setScrollbarFadingEnabled(false);
        webView.getSettings().setBuiltInZoomControls(true);
        		//Additional Webview Properties 
        	        webView.getSettings().setJavaScriptCanOpenWindowsAutomatically(true);
		        webView.getSettings().setDatabaseEnabled(true);
		        webView.getSettings().setAllowUniversalAccessFromFileURLs(true);
		        webView.getSettings().setAppCacheEnabled(true);
		        webView.getSettings().setLayoutAlgorithm(webView.getSettings().getLayoutAlgorithm().NORMAL);
		        webView.getSettings().setLoadWithOverviewMode(true);
		        webView.getSettings().setUseWideViewPort(false);
		        webView.setSoundEffectsEnabled(true);
		        webView.setHorizontalFadingEdgeEnabled(false);
		        webView.setKeepScreenOn(true);
		        webView.setScrollbarFadingEnabled(true);
		        webView.setVerticalFadingEdgeEnabled(false);
	
        
        
        
        
        
        */
         
        /*
         String summary = "<html><body>You scored <b>192</b> points.</body></html>";
         webview.loadData(summary, "text/html", null);
         */
         
        //Load url in webview
        webView.loadUrl(url);
          
          
    }
    
    
     
    // Open previous opened link from history on webview when back button pressed
     
    @Override
    // Detect when the back button is pressed
    public void onBackPressed() {
        if(webView.canGoBack()) {
            webView.goBack();
        } else {
            // Let the system handle the back button
            super.onBackPressed();
        }
    }

}
