export { apiGet, apiPostItem, apiDelete, webSocketConnect, getWebsocketInfo, HTTPError, appSettings }

const settingsResponse = await fetch("/api/settings")
const appSettings = await settingsResponse.json()

class HTTPError extends Error {
    constructor(code, message) {
        super(message)
        this.code = code
    }
}

async function apiGet(url) {
    const response = await fetch(url, {
        method: 'get',
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow"
    })

    if (!response.ok) {
        throw new HTTPError(response.status, response.statusText)
    }

    return await response.json()
}

async function apiPostItem(url, body) {
    const response = await fetch(url, {
        method: 'post',
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow",
        body: JSON.stringify(body)
    })

    if (!response.ok) {
        throw new HTTPError(response.status, response.statusText)
    }

    return await response.json()
}

async function apiDelete(url) {
    const response = await fetch(url, {
        method: 'delete',
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow"
    })

    if (!response.ok) {
        throw new HTTPError(response.status, response.statusText)
    }
}
async function getWebsocketInfo() {
    return await apiGet("/api/websocketinfo")
}

function webSocketConnect(connectionInfo, data_updater){
    let notify_websocket = null
    if (connectionInfo.protocol) {
        notify_websocket = new WebSocket(connectionInfo.url, connectionInfo.protocol)
    } else {
        notify_websocket = new WebSocket(connectionInfo.url)
    }

    notify_websocket.onopen = (event) => {
        console.log(`Connection opened: url: ${connectionInfo.url}, protocol: ${connectionInfo.protocol}`);
    }

    notify_websocket.onclose = (event) => {
        console.log("Connection closed - try to reconnect");
        notify_websocket.close();
        setTimeout(webSocketConnect, 500, connectionInfo, data_updater);
    }

    notify_websocket.onmessage = (event) => {
        console.log("WebSocket Message received");

        let new_data = convertMessage(JSON.parse(event.data), connectionInfo.protocol)

        if (new_data && new_data.length) {
            console.log(new_data)

            if (data_updater) {
                data_updater(new_data)
            }
        }
    }
  }

  function convertMessage(message, protocol) {
    if (protocol != "json.webpubsub.azure.v1") {
        return message
    }

    console.log(`Received Web PubSub message. type: ${message.type}`)
    if (message.type == "message" && message.from == "server" && message.dataType == "json") {
        return message.data
    }

    return []
  }