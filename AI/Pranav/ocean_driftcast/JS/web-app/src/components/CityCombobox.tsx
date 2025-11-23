/**
 * City Combobox Component
 *
 * Searchable dropdown with fuzzy matching and keyboard navigation.
 */

import React, { useState, useRef, useEffect } from 'react';
import Fuse from 'fuse.js';
import { CityData } from '../particles';

interface CityComboboxProps {
  cities: CityData[];
  onSelect: (city: CityData) => void;
  disabled?: boolean;
}

export const CityCombobox: React.FC<CityComboboxProps> = ({ cities, onSelect, disabled = false }) => {
  const [searchText, setSearchText] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [filteredCities, setFilteredCities] = useState<CityData[]>(cities);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fuzzy search with Fuse.js
  const fuse = useRef(new Fuse(cities, {
    keys: ['city', 'region'],
    threshold: 0.4,
    includeScore: true
  }));

  // Update fuse when cities change
  useEffect(() => {
    fuse.current.setCollection(cities);
    setFilteredCities(cities);
  }, [cities]);

  // Filter cities based on search text
  useEffect(() => {
    if (!searchText.trim()) {
      setFilteredCities(cities);
      setSelectedIndex(0);
      return;
    }

    const results = fuse.current.search(searchText);
    const matches = results.map(result => result.item);

    if (matches.length === 0) {
      setFilteredCities(cities);
    } else {
      setFilteredCities(matches);
    }

    setSelectedIndex(0);
  }, [searchText, cities]);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
    if (!isOpen) setIsOpen(true);
  };

  // Handle input focus
  const handleFocus = () => {
    setIsOpen(true);
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, filteredCities.length - 1));
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;

      case 'Enter':
        e.preventDefault();
        if (filteredCities[selectedIndex]) {
          handleSelect(filteredCities[selectedIndex]);
        }
        break;

      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        inputRef.current?.blur();
        break;

      default:
        break;
    }
  };

  // Handle city selection
  const handleSelect = (city: CityData) => {
    setSearchText(city.city);
    setIsOpen(false);
    onSelect(city);
  };

  // Handle Load City button
  const handleLoadClick = () => {
    if (filteredCities[selectedIndex]) {
      handleSelect(filteredCities[selectedIndex]);
    } else if (filteredCities[0]) {
      handleSelect(filteredCities[0]);
    }
  };

  return (
    <div className="city-combobox" ref={dropdownRef}>
      <label>Select City</label>

      <div className="combobox-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={searchText}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onKeyDown={handleKeyDown}
          placeholder="Search cities..."
          disabled={disabled}
          className="combobox-input"
        />

        <button
          className="dropdown-button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          aria-label="Toggle dropdown"
        >
          <span className={`arrow ${isOpen ? 'up' : 'down'}`}>▼</span>
        </button>
      </div>

      {isOpen && (
        <div className="dropdown-list">
          {filteredCities.slice(0, 10).map((city, index) => (
            <div
              key={city.city}
              className={`dropdown-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleSelect(city)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="city-name">{city.city}</span>
              <span className="city-type">{city.type}</span>
            </div>
          ))}
        </div>
      )}

      <button
        className="load-city-button"
        onClick={handleLoadClick}
        disabled={disabled || !searchText}
      >
        Load City
      </button>
    </div>
  );
};
