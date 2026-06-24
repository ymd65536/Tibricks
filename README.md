# Azure Template Repo README

## PoCの概要

```text
Kubernetesの複数PodからTiDBに対してデータを投入してTiDBのスケーリングを検証しつつ、Databricksを使ってTiDBを可視化します。挿入されたデータが正しく可視化されることを確認することで、TiDBのスケーリングが正しく行われていることを検証したいです。
また、挿入したデータをAIが読めるようにすることで、AIがTiDBのデータを活用できることを検証します。
構築手順はおおまかに以下の通りです。

1.TiDB Cloudにデータベースを作成
  pytidbで対応する
2.KubernetesのPodからTiDB Cloudに対してデータを投入
  pytidbでTiDB Cloudにデータを挿入
3.TiDB CloudとDatabricksを接続する
  コンソール上で設定するのでAIによる対応は不要
4.DatabricksでTiDB Cloudのデータを可視化
  コンソール上で設定するのでAIによる対応は不要だが、サンプルコードは必要
5.DatabricksのカタログにTiDBを登録する
  コンソール上で設定するのでAIによる対応は不要だが、サンプルコードは必要
6.カタログに登録したデータをAIに読ませる
  サンプルコードが必要

開発環境は以下の通りです。

ローカル環境
ツール: Rancher Desktop
言語: Python 3.11(uvを利用)
インフラ: Kubernetes

クラウド
Azure Databricks, TiDB Cloud

注意点

- 秘匿情報は `.env` に記載し、それ以外には記載しないこと
```

## ローカル環境の作業

- uvは `.venv` に仮想環境を作成してください
- サンプルコードはデータを挿入するだけの簡単なものでOKです。データベースの作成/データを挿入するだけのコードを作成してください。データベースの作成は pytidb でお願いします。最初の実行は uv の仮想環境で行ってください。
- 作成したスクリプトは Dockerfile で実行できるようにしてください。docker 上では uv ではなく python3 で実行できるようにしてください。
- 作成した Dockerfile を使って、Kubernetes の Pod を作成できるようにマニフェストを作成してください。マニフェストは yaml 形式で作成してください。
  - Pod の中でスクリプトを実行して TiDB Cloud にデータを挿入する手順を README に記載してください

## 1. ローカル実行手順

### 1.1 依存関係の準備

まずは uv を使って仮想環境を作成し、依存関係をインストールしてください。

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

これで、準備が整いました。

### 1.2 環境変数の設定

次に、`.env_sample` をコピーして `.env` を作成してください。`.env`を作成する方法は以下の通りです。

```bash
cp .env_sample .env
```

`.env` で次の変数を設定してください。この変数を使ってTiDB Cloud に接続します。

```text
TIDB_HOST=your-tidb-host
TIDB_PORT=4000
TIDB_USER=root
TIDB_PASSWORD=your-tidb-password
TIDB_DATABASE=sample
BATCH_SIZE=10
```

### 1.3 実行

```bash
python3 src/tidb_loader.py
```

## 2. Docker での実行

```bash
docker build -t tidb-loader:latest .
docker run --rm --env-file .env tidb-loader:latest
```

## 3. Kubernetes での実行

### 3.1 Docker イメージをローカルに読み込む

```bash
kind load docker-image tidb-loader:latest
```

### 3.2 Secret を作成

```bash
kubectl create secret generic tidb-credentials \
  --from-literal=TIDB_HOST='<your-tidb-host>' \
  --from-literal=TIDB_USER='<your-tidb-user>' \
  --from-literal=TIDB_DATABASE='<your-tidb-database>' \
  --from-literal=TIDB_PASSWORD='<your-tidb-password>'
```

`k8s/tidb-secret.yaml` は雛形です。実際の値はリポジトリへコミットせず、上の `kubectl create secret` コマンドや Kubernetes の Secret 管理機能で安全に設定してください。

`POD_NAME` は Pod の名前を自動で渡すための環境変数です。スクリプトではこの値を使って、どの Pod からデータを挿入したかを識別できます。

### 3.3 Pod を作成

```bash
kubectl apply -f k8s/tidb-loader-pod.yaml
```

### 3.4 実行結果を確認

```bash
kubectl logs pod/tidb-loader-pod
```

## 4. Databricks 連携のサンプル

Databricks では、TiDB から読み込んだデータを SQL で確認できます。

```sql
SELECT * FROM sensor_events LIMIT 10;
```

## 5. 参考

- [pytidb - GitHub](https://github.com/pingcap/pytidb)
