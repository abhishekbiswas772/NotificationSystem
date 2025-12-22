package configs

import (
	"context"
	"log"
	"os"
	"github.com/redis/go-redis/v9"
)

var (
	RedisClient *redis.Client
	Ctx         = context.Background()
)

func ConnectRedisClient() *redis.Client {
	once.Do(
		func() {
			redisAddr := os.Getenv("REDIS_ADDR")
			if redisAddr == "" {
				redisAddr = "localhost:6379"
			}

			RedisClient = redis.NewClient(&redis.Options{
				Addr:     redisAddr,
				Password: os.Getenv("REDIS_PASSWORD"),
				DB:       0,
			})

			if err := RedisClient.Ping(Ctx).Err(); err != nil {
				log.Fatalf("Redis connection failed: %v", err)
			}
			log.Println("Redis connected successfully")
		},
	)
	return RedisClient
}