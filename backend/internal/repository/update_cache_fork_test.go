//go:build unit

package repository

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
	"github.com/stretchr/testify/require"
)

func TestUpdateCacheIgnoresLegacyUpstreamMetadata(t *testing.T) {
	server := miniredis.RunT(t)
	rdb := redis.NewClient(&redis.Options{Addr: server.Addr()})
	t.Cleanup(func() { _ = rdb.Close() })
	ctx := context.Background()
	cache := NewUpdateCache(rdb)

	// An existing installation may still have upstream metadata for 20 minutes.
	require.NoError(t, rdb.Set(ctx, "update:latest", "upstream release metadata", time.Hour).Err())
	_, err := cache.GetUpdateInfo(ctx)
	require.ErrorIs(t, err, redis.Nil)

	require.NoError(t, cache.SetUpdateInfo(ctx, "fork release metadata", time.Hour))
	info, err := cache.GetUpdateInfo(ctx)
	require.NoError(t, err)
	require.Equal(t, "fork release metadata", info)
	legacy, err := rdb.Get(ctx, "update:latest").Result()
	require.NoError(t, err)
	require.Equal(t, "upstream release metadata", legacy)
}
