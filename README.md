# Liquify Thornode API

## Overview

The Liquify Thornode API provides easy access to historical and real-time data from THORChain. It includes information on network status, node performance, churn history, and staking details.

### Swagger URL

https://apiv2.liquify.com/thor/api/docs

### Features

- Historical Network Data: Access past churns, price data, max effective stake, and total bonded RUNE.

- Node Insights: Retrieve node-specific data like bond history, rewards, slashes, and churn positions.

- Network Statistics: Get the current block height, average block time, Coingecko RUNE data, and halted chain statuses.

- Node States: Check the status of active, standby, disabled, and whitelisted nodes.

## Example Endpoints

#### Get past churns
GET /historic/network/grabChurns

#### Get node rewards
GET /historic/node/grab-rewards/{node}

#### Get current network info
GET /network/dumpNetworkInfo

#### Get all active nodes
GET /nodes/getActive

