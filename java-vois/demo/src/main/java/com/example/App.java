package com.example;

import com.microsoft.playwright.*;
import java.nio.file.Paths;

/**
 * Hello world!
 *
 */
public class App 
{

    public static void main( String[] args ) {
    try (Playwright playwright = Playwright.create()) {
            BrowserType chromium = playwright.chromium();
            Browser browser = chromium.launch(new BrowserType.LaunchOptions().setHeadless(false)); // Set to false if you want to see the browser UI
            Page page = browser.newPage();
            page.navigate("http://google.com");
            page.waitForTimeout(5000);
            page.screenshot(new Page.ScreenshotOptions().setPath(Paths.get("example.png")));
            browser.close();
        }
    }
}
