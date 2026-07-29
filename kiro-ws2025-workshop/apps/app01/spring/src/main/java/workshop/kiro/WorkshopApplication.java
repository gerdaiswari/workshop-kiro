package workshop.kiro;

import java.net.InetAddress;
import java.time.Instant;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class WorkshopApplication {
    public static void main(String[] args) {
        SpringApplication.run(WorkshopApplication.class, args);
    }

    @RestController
    @RequestMapping("/api")
    static class InfoController {
        @GetMapping("/info")
        Map<String, String> info() throws Exception {
            return Map.of(
                "status", "ok",
                "application", "kiro-windows-upgrade-api",
                "marker", "SPRING_OK_V1",
                "host", InetAddress.getLocalHost().getHostName(),
                "time", Instant.now().toString()
            );
        }
    }
}
