import './index.css';
import React from 'react';
import { createRoot } from 'react-dom/client';
import InventoryList from './InventoryList';

const root = createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <InventoryList />
  </React.StrictMode>
);
