const mongoose = require("mongoose");

const gameSchema = new mongoose.Schema({
  title: { type: String, required: true },
  categories: { type: [String], default: [] },
  short_description: { type: String, required: true },
  full_description: { type: String },
  screenshots: { type: [String], default: [] },
  header_image: { type: String },
  rating: { type: String, default: "N/A" },
  publisher: { type: String, default: "" },
  platforms: { type: String },
  release_date: { type: String },
  prices: { type: Map, of: String },
});

module.exports = GameInfo = mongoose.model("GameInfo", gameSchema, "games_info");
