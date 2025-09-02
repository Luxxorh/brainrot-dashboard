import fetch from "node-fetch";

const URL = "https://brainrotss.up.railway.app/brainrots";
const MAX_PLAYERS = 8;
const HEADERS = {
  "User-Agent": "Mozilla/5.0",
  Accept: "application/json",
  "Cache-Control": "no-cache",
};

async function fetchLiveServers() {
  try {
    const resp = await fetch(URL, { headers: HEADERS, timeout: 1000 });
    const data = (await resp.json()) || [];

    const serverCache = {};
    data.forEach(s => {
      if (s.jobId && s.serverId) {
        serverCache[s.jobId] = { name: s.name, placeId: s.serverId };
      }
    });

    const placeMap = {};
    Object.entries(serverCache).forEach(([jobId, info]) => {
      if (!placeMap[info.placeId]) placeMap[info.placeId] = [];
      placeMap[info.placeId].push(jobId);
    });

    const updated = [];

    for (const [placeId, jobIds] of Object.entries(placeMap)) {
      try {
        const r = await fetch(
          `https://games.roblox.com/v1/games/${placeId}/servers/Public?sortOrder=Asc&limit=100`,
          { headers: HEADERS, timeout: 1000 }
        );
        const servers = (await r.json()).data || [];

        servers.forEach(s => {
          const jobId = s.id;
          if (jobIds.includes(jobId)) {
            const players = s.playing || 0;
            const maxPlayers = s.maxPlayers || MAX_PLAYERS;
            const name = serverCache[jobId].name || "Unknown";
            const timestamp = new Date().toLocaleTimeString();
            const joinLink = `https://www.roblox.com/games/${placeId}/Steal-a-Brainrot?serverJobId=${jobId}`;
            updated.push({
              timestamp,
              name,
              placeId,
              jobId,
              players: `${players}/${maxPlayers}`,
              link: joinLink,
              created: Date.now(),
            });
          }
        });
      } catch (e) {
        continue;
      }
    }

    return updated.slice(0, 100);
  } catch (e) {
    return [];
  }
}

export default async function handler(req, res) {
  const data = await fetchLiveServers();
  res.setHeader("Content-Type", "application/json");
  res.status(200).json(data);
}
