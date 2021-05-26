# 实验设计及通信协议

- [实验设计及通信协议](#实验设计及通信协议)
  - [系统概述](#系统概述)
  - [训练模式](#训练模式)
    - [流程图](#流程图)
    - [消息定义](#消息定义)
  - [构造模型指令（有标签）](#构造模型指令有标签)
  - [构造模型指令（无标签）](#构造模型指令无标签)
  - [同步（有标签）模式](#同步有标签模式)
    - [流程图](#流程图-1)
    - [消息定义](#消息定义-1)
  - [异步（无标签）模式](#异步无标签模式)
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
   分别包括有标签、无标签两种模式，但两种模式在采集数据的过程中完全相同，因此在后台不作区分。

2. 构造模型指令

   用于告知后台使用 XXX 数据构造模型。
   在此消息中，需要告知后台使用有标签模型或无标签模式进行模型构造。

3. 同步（有标签）模式

   实验开始后，“游戏”程序通过打并口的方式向“后台”程序发送计算请求；
   “后台”程序接到要求后，根据近期脑电数据，计算并发送动作标签。

4. 异步（无标签）模式

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
     "dataPath": "[The Valid Path to Save the Data]" // 该SESSION结束后，数据将存储在这里
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
     "sessionName": "training"
   }
   ```

## 构造模型指令（有标签）

1. 开始构造消息

   由“主控”发送给“后台”，用于开始构造数据。

   消息约定

   ```json
   {
     "method": "startBuilding",
     "sessionName": "youbiaoqian",
     "dataPath": "[The Valid Path of the Data]", // 数据已存储在这里
     "modelPath": "[The Valid Path to Save the Model]" // 模型将存储在这里
   }
   ```

2. 结束消息

   由“后台”发送给“主控”，用于告知训练完毕。

   消息约定

   ```json
   {
     "method": "stopBuilding",
     "sessionName": "youbiaoqian",
     "validAccuracy": "0.95" // 训练模型时的正确率数值，正常情况下数值为 0-1 之间的浮点数，不正常情况下此数值为 -1 代表计算错误。
   }
   ```

## 构造模型指令（无标签）

1. 开始构造消息

   由“主控”发送给“后台”，用于开始构造数据。

   消息约定

   ```json
   {
     "method": "startBuilding",
     "sessionName": "wubiaoqian",
     "dataPath": "[The Valid Path of the Data]", // 数据已存储在这里
     "modelPath": "[The Valid Path to Save the Model]" // 模型将存储在这里
   }
   ```

2. 结束消息

   由“后台”发送给“主控”，用于告知训练完毕。

   消息约定

   ```json
   {
     "method": "stopBuilding",
     "sessionName": "wubiaoqian",
     "validAccuracy": "0.95" // 训练模型时的正确率数值，正常情况下数值为 0-1 之间的浮点数，不正常情况下此数值为 -1 代表计算错误。
   }
   ```

## 同步（有标签）模式

同步模式是有标签的在线实验，前若干个标签是用于更新数据（称为验证阶段），因此会对已有的模型进行更新。
模型更新过程在通信过程中有所体现。

### 流程图

>  <img src="./有标签模式.png" alt="./有标签模式.png" width="600px">
>
> 图 2 有标签模式示意图

### 消息定义

1. 开始采集消息

   由“主控”发送给“后台”，用于开始有标签模式。

   消息约定

   ```json
   {
     "method": "startSession",
     "sessionName": "youbiaoqian",
     "dataPath": "[The Valid Path to Save the Data]", // 该SESSION结束后，数据将存储在这里
     "modelPath": "[The Valid Path of the Model]", // 使用已有模型进行计算
     "newModelPath": "[The Valid Path to Save the Model]", // 该SESSION结束后，模型将存储在这里
     "updateCount": "4", // 验证的数量，4代表前4个标签是用于更新模型，之后才进行模型测试
     "totalCount": "10" // 总标签的数量，10代表总共会出现10个标签的动作，此数值会被后台忽略
   }
   ```

2. 计算标签消息

   由“游戏”以在脑电数据中打标签的形式发送给“后台”，用于要求后者计算动作标签。

3. 结束采集消息

   由“主控”发送给“后台”，用于结束异步模式。

   消息约定

   ```json
   {
     "method": "stopSession",
     "sessionName": "youbiaoqian"
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
     "sessionName": "youbiaoqian",
     "accuracy": "0.95" // 同步在线实验中的总体准确率数值，"0.95" 代表所有试次中，有95%的试次分类正确
   }
   ```

## 异步（无标签）模式

### 流程图

>  <img src="./无标签模式.png" alt="./无标签模式.png" width="600px">
>
> 图 3 无标签模式示意图

### 消息定义

1. 开始采集消息

   由“主控”发送给“后台”，用于开始同步模式。

   消息约定

   ```json
   {
     "method": "startSession",
     "sessionName": "wubiaoqian",
     "dataPath": "[The Valid Path to Save the Data]", // 该SESSION结束后，数据将存储在这里
     "modelPath": "[The Valid Path of the Model]", // 使用已有模型进行计算
     "totalCount": "10" // 总标签的数量，10代表总共会出现10个标签的动作，此数值会被后台忽略
   }
   ```

2. 结束采集消息

   由“主控”发送给“后台”，用于结束异步模式。

   消息约定

   ```json
   {
     "method": "stopSession",
     "sessionName": "wubiaoqian"
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
     "sessionName": "wubiaoqian"
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
> | 顺序     | detail 字段    | 典型情况                           |
> | -------- | -------------- | ---------------------------------- |
> | 1        | modelNotFound  | 模型不存在                         |
> | 2        | deviceError    | 无法获取脑电数据、或获取数据不正常 |
> | 3        | computeError   | 无法完成标签计算                   |
> | 4        | fileError      | 无法获取或存储数据                 |
> | $\infty$ | undefinedError | 不属于以上的其他错误情况           |

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
