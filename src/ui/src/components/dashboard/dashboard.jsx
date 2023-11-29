import React from 'react';
import { Navbar } from '../navbar';
import { SearchBox } from '../searchbox/searchbox';
import { Results } from '../results';
import { UserSuggestions } from '../usersuggestions';

export const Dashboard = () => {
  return (
    <>
      <Navbar />

      <SearchBox />

      <Results />

      <UserSuggestions />
    </>
  );
};
