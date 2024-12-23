const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config();

const gameRoutes = require("./routes/gameRoutes");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 5000;

// MongoDB connection
mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB connected"))
  .catch((err) =>
    console.log("----------Error connecting to MongoDB-----\n", err)
  );

// Routes
app.use("/api/games_info", gameRoutes);

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
