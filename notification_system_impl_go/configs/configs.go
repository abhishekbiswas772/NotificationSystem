package configs

import (
	"fmt"
	"log"
	"os"
	"strings"
	"sync"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var (
	DB      *gorm.DB
	dbOnce  sync.Once
	envOnce sync.Once
)

func loadEnv() {
	envOnce.Do(func() {
		data, err := os.ReadFile(".env")
		if err != nil {
			return
		}
		for _, line := range strings.Split(string(data), "\n") {
			line = strings.TrimSpace(line)
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			parts := strings.SplitN(line, "=", 2)
			if len(parts) != 2 {
				continue
			}
			key := strings.TrimSpace(parts[0])
			val := strings.TrimSpace(parts[1])
			if key == "" {
				continue
			}
			if _, exists := os.LookupEnv(key); exists {
				continue
			}
			_ = os.Setenv(key, val)
		}
	})
}

func getenvDefault(key, fallback string) string {
	if val, ok := os.LookupEnv(key); ok && val != "" {
		return val
	}
	return fallback
}

func buildDSN() string {
	host := getenvDefault("DB_HOST", "localhost")
	port := getenvDefault("DB_PORT", "5432")
	user := getenvDefault("DB_USER", "postgres")
	password := os.Getenv("DB_PASSWORD")
	name := getenvDefault("DB_NAME", "postgres")
	sslmode := getenvDefault("DB_SSLMODE", "disable")
	channelBinding := os.Getenv("DB_CHANNELBINDING")
	dsn := fmt.Sprintf("postgresql://%s:%s@%s:%s/%s?sslmode=%s", user, password, host, port, name, sslmode)
	if channelBinding != "" {
		dsn = fmt.Sprintf("%s&channel_binding=%s", dsn, channelBinding)
	}
	return dsn
}

func ConnectDatabase() *gorm.DB {
	dbOnce.Do(func() {
		loadEnv()
		dsn := os.Getenv("DATABASE_URL")
		if dsn == "" {
			dsn = buildDSN()
		}
		if dsn == "" {
			log.Fatal("database configuration is not present")
		}
		database, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
			NamingStrategy: nil, // Use default GORM naming (snake_case)
		})
		if err != nil {
			log.Fatal("Fail to connect database: ", err)
		}
		DB = database
		log.Println("Database connected")
	})
	return DB
}
