# 实验设计及通信协议

- [实验设计及通信协议](#实验设计及通信协议)
  - [系统概述](#系统概述)
  - [训练模式](#训练模式)
    - [流程图](#流程图)
    - [消息定义](#消息定义)
  - [异步模式](#异步模式)
    - [流程图](#流程图-1)
    - [消息定义](#消息定义-1)
  - [同步模式](#同步模式)
    - [流程图](#流程图-2)
    - [消息定义](#消息定义-2)
  - [其他消息](#其他消息)
    - [心跳包消息](#心跳包消息)
    - [无法识别消息](#无法识别消息)
    - [无法执行消息](#无法执行消息)

## 系统概述

实验系统由“主控”（薛）、“后台”（张）和“采集”（脑电设备）三部分组成。
其中，

- 由“主控”搭建 TCP 服务器，其他参与者以 client 的形式与之通信；
- “后台”仅与“主控”进行通信；
- “主控”和“游戏”之间进行其他必要的通信；
  - “游戏”通过并口向“采集”设备发送实验标签；
  - 由于“后台”只与“主控”进行通信，因此“游戏”的相关功能在“后台”的视角看来，是由“主控”进行协调和完成的；
- “后台”根据需要获取“采集”设备的实时数据。

实验分为三种模式，分别为

1. 训练模式

   用于用户在正式使用前进行算法训练。

2. 异步模式

   实验开始后，“主控”程序向“后台”程序发送计算请求；
   “后台”程序接到要求后，根据近期脑电数据，计算并发送动作标签。

3. 同步模式

   实验开始后，“后台”程序周期性地，主动向“主控”程序发送动作标签；
   动作标签是对连续的脑电数据进行加窗而计算得到的。

## 训练模式

### 流程图

>  <img src="./训练模式.png" alt="./训练模式.png" width="600px">
>
> 图 1 训练模式示意图

### 消息定义

1. 开始采集消息

   由“主控”发送给“后台”，用于开始训练模式。

   消息约定

   ```json
   {
     "method": "startSession",
     "sessionName": "training",
     "dataPath": "./data/latestData.csv", // 实验数据将存储于此，目录应存在，文件应不存在
     "modelPath": "./module/latestModel.csv" // 模型数据将存储于此，目录应存在，文件应不存在
   }
   ```

2. 结束采集消息

   由“主控”发送给“后台”，用于结束训练模式。

   消息约定

   ```json
   {
     "method": "stopSession",
     "sessionName": "training"
   }
   ```

3. 结束消息

   由“后台”发送给“主控”，用于告知数据与模型存储完毕。

   消息约定

   ```json
   {
     "method": "sessionStopped",
     "sessionName": "training",
     "dataPath": "./data/latestData.csv", // 实验数据已存储于此
     "modelPath": "./module/latestModel.csv" // 模型数据已存储于此
   }
   ```

## 异步模式

### 流程图

>  <img src="./异步模式.png" alt="./异步模式.png" width="600px">
>
> 图 2 训练模式示意图

### 消息定义

1. 开始采集消息

   由“主控”发送给“后台”，用于开始异步模式。

   消息约定

   ```json
   {
     "method": "startSession",
     "sessionName": "asynchronous",
     "dataPath": "./data/latestData.csv", // 实验数据将存储于此，目录应存在，文件应不存在
     "modelPath": "./module/latestModel.csv" // 模型数据，文件应存在
   }
   ```

2. 计算标签消息

   由“主控”发送给“后台”，用于要求后者计算动作标签。
   包括“验证”和“测试”两种模式，“主控”应根据情况主动发送正确的模式内容。

   消息约定

   ```json
   {
     "method": "computeLabel",
     "mode": "valid" // 模式标签，"valid":验证; "test":测试.
   }
   ```

3. 结束采集消息

   由“主控”发送给“后台”，用于结束异步模式。

   消息约定

   ```json
   {
     "method": "stopSession",
     "sessionName": "asynchronous"
   }
   ```

4. 标签消息

   由“后台”发送给“主控”，用于告知动作标签。

   消息约定

   ```json
   {
     "method": "labelComputed",
     "label": "1" // "1" refers motion; "0" refers no motion
   }
   ```

5. 结束消息

   由“后台”发送给“主控”，用于告知数据存储完毕。

   消息约定

   ```json
   {
     "method": "sessionStopped",
     "sessionName": "asynchronous",
     "dataPath": "./data/latestData.csv" // 实验数据已存储于此
   }
   ```

## 同步模式

### 流程图

>  <img src="./同步模式.png" alt="./同步模式.png" width="600px">
>
> 图 2 训练模式示意图

### 消息定义

1. 开始采集消息

   由“主控”发送给“后台”，用于开始同步模式。

   消息约定

   ```json
   {
     "method": "startSession",
     "sessionName": "synchronous",
     "dataPath": "./data/latestData.csv", // 实验数据将存储于此，目录应存在，文件应不存在
     "modelPath": "./module/latestModel.csv" // 模型数据，文件应存在
   }
   ```

2. 结束采集消息

   由“主控”发送给“后台”，用于结束异步模式。

   消息约定

   ```json
   {
     "method": "stopSession",
     "sessionName": "synchronous"
   }
   ```

3. 标签消息

   由“后台”发送给“主控”，用于告知动作标签。
   由于采用“同步”模式，本消息由“后台”**自主地**、**周期性**地发送给主控。

   消息约定

   ```json
   {
     "method": "labelComputed",
     "label": "1" // "1" refers motion; "0" refers no motion
   }
   ```

4. 结束消息

   由“后台”发送给“主控”，用于告知数据存储完毕。

   消息约定

   ```json
   {
     "method": "sessionStopped",
     "sessionName": "synchronous",
     "dataPath": "./data/latestData.csv" // 实验数据已存储于此
   }
   ```

## 其他消息

### 心跳包消息

心跳包消息用于保持 TCP 连接，由通信能与者按需发送，频率不宜过快。
接到心跳包后，需要发送心跳回复包，为避免消息死循环，不可回复心跳回复包。

消息约定

- 心跳包：

```json
{
  "method": "keepAlive",
  "count": "0"
}
```

- 心跳回复包：

```json
{
  "method": "keepAlive",
  "count": "1"
}
```

### 无法识别消息

由于本系统包含多种实验模式和信息种类，约定将以下消息作为无法识别消息：

- 不属于当前实验模式的合法消息；
  - 如“训练模式”过程中，收到“异步模式”的消息；
  - 如“同步模式”过程中，收到“计算标签”的消息；
  - ……
- 不满足本约定的所有非法消息。

接到“无法识别消息”后，接收端应积极回复“消息无法识别”错误反馈消息。

消息约定：

```json
{
  "method": "error",
  "reason": "invalidMessage",
  "raw": "{...}", // 建议将收到的消息原封不动写在这里，方便对方DEBUG
  "comment": "bala bala" // 其他有用信息
}
```

### 无法执行消息

由于本系统涉及数据流及文件操作，如

- 脑电数据获取；
- 数据文件存储；
- 模型文件读取；
- ……

如遇到文件应存在却不存在，或要存储的目录不存在的情况，需要将其视为“无法执行消息”。
另外，如遇到无法从脑电设备获取数据的情况，也属于“无法执行消息”。

接到“无法执行消息”后，接收端应积极回复“消息无法执行”错误反馈消息。

消息约定：

```json
{
  "method": "error",
  "reason": "operationFailed",
  "detail": "--", // [见后表]
  "raw": "{...}", // 建议将收到的消息原封不动写在这里，方便对方处理
  "comment": "bala bala" // 其他有用信息
}
```

由于运行时遇到的情况千奇百怪，现将可能的情况枚举如下：

> 表 1、Detail 字段典型值对照表
>
> | 顺序     | detail 字段    | 典型情况                 |
> | -------- | -------------- | ------------------------ |
> | 1        | folderInvalid  | 应存在的目录不存在       |
> | 2        | fileInvalid    | 应存在的文件不存在       |
> | 3        | fileExists     | 不应存在的文件存在       |
> | 4        | fileWrong      | 无法正常载入文件         |
> | 5        | deviceError    | 无法获取合格的脑电数据   |
> | 6        | computeError   | 无法完成标签计算         |
> | $\infty$ | undefinedError | 不属于以上的其他错误情况 |

注：在实际使用过程中，错误检查的顺序与上表相同，遇到错误立即返回，不再继续进行后续检查；
另外，在实际使用中也可能出现多个错误均有可能性的情况，将使用多个 detail 字段进行描述；

举例

```json
{
  "method": "error",
  "reason": "operationFailed",
  "detail": "folderInvalid, fileExists", // 代表目录无效或文件存在，两个错误均有可能已经发生
  "raw": "{...}",
  "comment": "bala bala"
}
```
