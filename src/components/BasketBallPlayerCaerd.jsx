import React from "react";
import "../styles/BasketballPlayerCard.css";

const BasketballPlayerCard = ({ name, image, position, stats }) => {
  return (
    <div className="player-card">
      <img src={image} alt={`${name}`} className="player-image" />
      <h2 className="player-name">{name}</h2>
      <p className="player-position">{position}</p>
      <div className="player-stats">
        <h4>Points per Game</h4>
        <p> {stats.pointsPerGame}</p>
        <h4>Assists per Game</h4>
        <p>{stats.assistsPerGame}</p>

        <h4>Rebounds per Game</h4>

        <p> {stats.reboundsPerGame}</p>
      </div>
    </div>
  );
};

export default BasketballPlayerCard;
