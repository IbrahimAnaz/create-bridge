const bedrock = require('bedrock-protocol');

console.log('[DummyClient] Starting connection to 127.0.0.1:19132 as DummyBot...');

const client = bedrock.createClient({
  host: '127.0.0.1',
  port: 19132,
  username: 'DummyBot',
  offline: true,
  skipPing: true
});

let packetCounts = {};
let spawned = false;
let chunksReceived = 0;

client.on('connect', () => {
  console.log('[DummyClient] Connected to RakNet server!');
});

client.on('start_game', (packet) => {
  console.log(`[DummyClient] START_GAME received! RuntimeEntityId: ${packet.runtime_entity_id}, Pos:`, packet.player_position);
});

client.on('level_chunk', (packet) => {
  chunksReceived++;
  if (chunksReceived <= 5 || chunksReceived % 20 === 0) {
    console.log(`[DummyClient] Received level_chunk #${chunksReceived} at chunk (${packet.x}, ${packet.z})`);
  }
});

client.on('play_status', (packet) => {
  console.log('[DummyClient] PLAY_STATUS:', packet.status);
  if (packet.status === 'player_spawn') {
    spawned = true;
    console.log('[DummyClient] >>> PLAYER_SPAWN SUCCESS! Spawned in world! <<<');
  }
});

client.on('add_item_entity', (packet) => {
  console.log('[DummyClient] [PACKET] add_item_entity received:', {
    runtime_entity_id: packet.runtime_entity_id,
    item: packet.item?.network_id,
    pos: packet.position
  });
});

client.on('add_entity', (packet) => {
  console.log('[DummyClient] [PACKET] add_entity received:', {
    id: packet.identifier,
    runtime_entity_id: packet.runtime_entity_id,
    pos: packet.position
  });
});

client.on('packet', (deserialized) => {
  const name = deserialized.data?.name;
  if (name) {
    packetCounts[name] = (packetCounts[name] || 0) + 1;
  }
});

client.on('disconnect', (packet) => {
  console.log('[DummyClient] Disconnected from server:', packet);
});

client.on('kick', (packet) => {
  console.log('[DummyClient] Kicked:', packet);
});

client.on('error', (err) => {
  console.error('[DummyClient] Error:', err);
});

setTimeout(() => {
  console.log('\n[DummyClient] ================= TEST SUMMARY (20s) =================');
  console.log('Spawned into world:', spawned);
  console.log('Total level_chunks received:', chunksReceived);
  console.log('Total packet types received:');
  const sorted = Object.entries(packetCounts).sort((a, b) => b[1] - a[1]);
  for (const [pName, count] of sorted.slice(0, 15)) {
    console.log(`  - ${pName}: ${count}`);
  }
  console.log('==================================================================');
  client.close();
  process.exit(0);
}, 20000);
