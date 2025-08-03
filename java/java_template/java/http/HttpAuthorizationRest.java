package http;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Base64;

import org.apache.commons.lang3.StringUtils;
import org.apache.log4j.ConsoleAppender;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;

public class HttpAuthorizationRest {
    private static final Logger logger = Logger.getLogger(HttpAuthorizationRest.class);
    static {
        Logger.getRootLogger().addAppender(new ConsoleAppender(new PatternLayout("[%d{HH:mm:ss}] %p %c{1}:%L - %m%n")));
    }

    public static void main(String[] args) {
        URL url = null;
        try {
            url = new URL("http://apradm09.hyundaicapital.com:25000/queries");
            String encoding = Base64.getEncoder().encodeToString(new String("admin:admin_password").getBytes());

            HttpURLConnection conn = (HttpURLConnection)url.openConnection();
            conn.setRequestMethod("GET");
            conn.setDoOutput(true);
            conn.setRequestProperty("Authorization", "Basic " + encoding);

            try (InputStream content = (InputStream)conn.getInputStream()) {
                BufferedReader in = new BufferedReader(new InputStreamReader(content));

                String line = null;
                int queryActiveCount = 0;
                while( (line = in.readLine()) != null ) {
                    if (line.contains("queries in flight")) {
                        //System.out.println(line);
                        queryActiveCount = Integer.parseInt( StringUtils.substringBetween(line, "<h3>", " queries in flight</h3>").trim() );
                        break;
                    }
                }

                System.out.println("queryActiveCount : " + queryActiveCount);
            }

            conn.disconnect();
        } catch(Throwable e) {
            logger.error(e.getMessage(), e);
        }
    }
}
