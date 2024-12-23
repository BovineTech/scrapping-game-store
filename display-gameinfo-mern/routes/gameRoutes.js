const express = require("express");
const GameInfo = require("../models/Game");
const router = express.Router();

// Fetch all games with optional filters
router.get("/", async (req, res) => {
  const { platform, region, category, sort } = req.query;
  let filter = {};

  if (platform) filter.platforms = platform;
  if (category) filter.category = category;

  try {
    let games = await GameInfo.find({});
    if (sort) {
      games = games.sort((a, b) => b[sort] - a[sort]); // Example sort by rating or price
    }
    res.status(200).json(games);
    console.log("Game Routing", games);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
