package repository

import (
	"context"
	"time"

	"github.com/Wei-Shaw/sub2api/internal/service"
	"github.com/redis/go-redis/v9"
)

// Keep upstream release metadata from being reused after migrating to this fork.
const updateCacheKey = "update:latest:" + service.UpdateRepository

type updateCache struct {
	rdb *redis.Client
}

func NewUpdateCache(rdb *redis.Client) service.UpdateCache {
	return &updateCache{rdb: rdb}
}

func (c *updateCache) GetUpdateInfo(ctx context.Context) (string, error) {
	return c.rdb.Get(ctx, updateCacheKey).Result()
}

func (c *updateCache) SetUpdateInfo(ctx context.Context, data string, ttl time.Duration) error {
	return c.rdb.Set(ctx, updateCacheKey, data, ttl).Err()
}
