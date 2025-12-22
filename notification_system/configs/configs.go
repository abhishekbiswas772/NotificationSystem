package configs

import (
	"log"
	"os"
	"sync"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var (
	DB *gorm.DB
	once sync.Once
)

func ConnectDatabase() *gorm.DB {
	once.Do(func() {
		dsn := os.Getenv("DATABASE_URL")
		if dsn == "" {
			log.Fatal("DATABASE_URL is not present")
		}
		database, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
		if err != nil {
			log.Fatal("Fail to connect database: ", err)
		}
		DB = database
		log.Println("Database connected")
	})
	return DB
}