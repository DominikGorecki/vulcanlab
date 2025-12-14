/**
 * Settings page - Main settings component.
 *
 * Contains various settings sections including conversion settings.
 */

import React from 'react';
import { ConversionSettings } from './ConversionSettings';

export const Settings: React.FC = () => {
  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <section className="settings-section">
        <ConversionSettings />
      </section>

      {/* Other settings sections can be added here */}
    </div>
  );
};
