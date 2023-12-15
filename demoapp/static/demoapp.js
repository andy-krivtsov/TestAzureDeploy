const API_PATH = '/messages/'
const WS_PATH = '/view/feed'

const REFRESH_DELAY = 1000
let last_version = null

function getWebSocketUrl() {
  scheme = window.location.protocol == "https:" ? "wss://" : "ws://"
  return scheme + window.location.host + WS_PATH
}

async function sendMessage(msg) {
  const response = await fetch(API_PATH, {
      method: 'post',
      headers: {
        "Content-Type": "application/json"
      },
      redirect: "follow",
      body: JSON.stringify(msg)
  })

  if(!response.ok) {
    throw new Error(`Status: ${response.status}, text: ${response.statusText}`)
  }

  await response.json()
}

async function newMessage(data = "Service Bus message text!") {
    msg = {
      id: crypto.randomUUID(),
      data: data
    }

    await sendMessage(msg)
    console.log(`Sent message: id = ${msg.id}`)
}

async function getMessages() {
  let url = last_version ? `${API_PATH}?last_version=${last_version}` : API_PATH

  const response = await fetch(url, {
      method: 'get',
      headers: {
        "Content-Type": "application/json"
      },
      redirect: "follow"
  })

  if(!response.ok) {
    throw new Error(`Status: ${response.status}, text: ${response.statusText}`)
  }

  return await response.json()
}

// async function updateTable(tableName = 'messages-table', newRowFunc) {
//   msg_list = await getMessages()
//   console.log(msg_list)

//   const table = $(`#${tableName}`)

//   msg_list.messages.forEach( msg_info => {
//     console.log(`Process msg: id=${msg_info.message.id}`)
//     console.log(msg_info)

//     row = table.bootstrapTable('getRowByUniqueId', msg_info.message.id)
//     if (!row) {
//       table.bootstrapTable('append', [ newRowFunc(msg_info) ])
//     } else {
//       table.bootstrapTable('updateByUniqueId', {
//         id : msg_info.message.id,
//         row: newRowFunc(msg_info),
//         replace: true
//       })
//     }
//   })
//   last_version = msg_list.version
//   setTimeout(updateTable, REFRESH_DELAY, tableName, newRowFunc)
// }

function updateTable(msg_list, newRowFunc, tableName = 'messages-table') {
  console.log("Update table")
  const table = $(`#${tableName}`)

  msg_list.forEach( msg_info => {
    console.log(`Process msg: id=${msg_info.message.id}`)
    console.log(msg_info)

    row = table.bootstrapTable('getRowByUniqueId', msg_info.message.id)
    if (!row) {
      table.bootstrapTable('append', [ newRow(msg_info) ])
    } else {
      table.bootstrapTable('updateByUniqueId', {
        id : msg_info.message.id,
        row: newRow(msg_info),
        replace: true
      })
    }
  })
}

function webSocketConnect(url, data_updater){
  const socket = new WebSocket(url)

  socket.onopen = (event) => {
      console.log(`Connection opened: ${url}`);
  }

  socket.onclose = (event) => {
      console.log("Connection closed - try to reconnect");
      socket.close();
      setTimeout(webSocketConnect, 500, url, data_updater);
  }

  socket.onmessage = (event) => {
      console.log(`Message received (${url})`);
      let new_data = JSON.parse(event.data)
      console.log(new_data)
      data_updater(new_data)
  }
}
