---
source: https://example.com/go-concurrency
title: Go 并发编程实战
date: 2026-06-15
tags: [Go, 并发, goroutine, channel]
topics: [backend]
---

# Go 并发编程实战

Go 语言通过 goroutine 和 channel 实现了简洁的并发模型。与传统的线程模型不同，goroutine 是用户态线程，启动成本极低（仅 2KB 栈空间），可以轻松启动数十万个。

## goroutine 的使用

```go
go func() {
    // 并发执行的任务
}()
```

使用 `go` 关键字即可启动一个 goroutine，无需复杂的线程管理 API。

## channel 通信

Go 的并发哲学是"不要通过共享内存来通信，而应该通过通信来共享内存"。channel 是 goroutine 之间的通信管道：

```go
ch := make(chan int, 10)  // 缓冲 channel
ch <- 42                   // 发送
val := <-ch                // 接收
```

## sync 包

对于需要共享内存的场景，Go 提供了 sync 包：

- `sync.Mutex` — 互斥锁
- `sync.RWMutex` — 读写锁
- `sync.WaitGroup` — 等待一组 goroutine 完成
- `sync.Once` — 只执行一次

## 选型建议

| 场景 | 推荐方案 |
|------|----------|
| 简单并发 | goroutine + WaitGroup |
| 生产者-消费者 | channel + select |
| 共享状态 | sync.Mutex + goroutine |
| 池化资源 | 带缓冲 channel |
| 超时控制 | context.WithTimeout |
