export { apiGet, apiPostItem, apiDelete, webSocketConnect, getWebsocketInfo }

async function apiGet(url) {
    const response = await fetch(url, {
        method: 'get',
        headers: {
            "Content-Type": "application/json"
        },
        redirect: "follow"
    })

    if (!response.ok) {
        throw new Error(`Status: ${response.status}, text: ${response.statusText}`)
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
        throw new Error(`Status: ${response.status}, text: ${response.statusText}`)
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
        throw new Error(`Status: ${response.status}, text: ${response.statusText}`)
    }
}
async function getWebsocketInfo() {
    return await apiGet("/api/websocketinfo")
}

function webSocketConnect(url, data_updater){
    const notify_websocket = new WebSocket(url)

    notify_websocket.onopen = (event) => {
        console.log(`Connection opened: ${url}`);
    }

    notify_websocket.onclose = (event) => {
        console.log("Connection closed - try to reconnect");
        notify_websocket.close();
        setTimeout(webSocketConnect, 500, url, data_updater);
    }

    notify_websocket.onmessage = (event) => {
        console.log(`Message received (${url})`);
        let new_data = JSON.parse(event.data)
        console.log(new_data)
        if (data_updater) {
            data_updater(new_data)
        }
    }
  }