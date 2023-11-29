import React, { useState } from 'react';
import './searchbox.css';
import {
  SearchField,
  TagsField,
  SearchButton,
  PaperComponentContainer,
  TagsOutfield,
} from './elements';
import InputAdornment from '@mui/material/InputAdornment';
import Autocomplete from '@mui/material/Autocomplete';
import SearchIcon from '@mui/icons-material/Search';
import SendIcon from '@mui/icons-material/Send';
import Stack from '@mui/material/Stack';

const quoteFinderTags = [
  { title: 'WisdomQuotes', value: 'wisdom' },
  { title: 'InspirationalQuotes', value: 'inspirational' },
  { title: 'MotivationalQuotes', value: 'motivational' },
  { title: 'LifeQuotes', value: 'life' },
  { title: 'PositiveVibes', value: 'positive' },
  { title: 'MindfulnessQuotes', value: 'mindfulness' },
  { title: 'SuccessQuotes', value: 'success' },
  { title: 'HappinessQuotes', value: 'happiness' },
  { title: 'LoveQuotes', value: 'love' },
  { title: 'SelfImprovement', value: 'self-improvement' },
  { title: 'EmpowermentQuotes', value: 'empowerment' },
  { title: 'CourageQuotes', value: 'courage' },
  { title: 'GratitudeQuotes', value: 'gratitude' },
  { title: 'LeadershipQuotes', value: 'leadership' },
  { title: 'Reflections', value: 'reflections' },
  { title: 'InnerPeace', value: 'inner-peace' },
  { title: 'DreamQuotes', value: 'dreams' },
  { title: 'StrengthQuotes', value: 'strength' },
  { title: 'ChangeQuotes', value: 'change' },
  { title: 'PurposefulLiving', value: 'purposeful-living' },
];

export const SearchBox = () => {
  const [open, setOpen] = useState(false);
  return (
    <div className="search-box">
      <Stack spacing={2} alignItems="center">
        <h1 className="search-title">What are you looking for ?</h1>

        <SearchField
          placeholder="Search"
          InputProps={{
            disableUnderline: true,
            startAdornment: (
              <InputAdornment
                position="start"
                sx={{ marginLeft: '15px', color: 'rgba(241, 241, 241, 0.3)' }}
              >
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />

        <TagsOutfield>
          <Autocomplete
            multiple
            id="tags-standard"
            options={quoteFinderTags}
            getOptionLabel={(option) => option.title}
            PaperComponent={PaperComponentContainer}
            open={open}
            onOpen={() => setOpen(true)}
            onClose={(event, reason) => {
              if (reason !== 'selectOption') {
                setOpen(false);
              }
            }}
            renderInput={(params) => (
              <TagsField {...params} placeholder="Tags" />
            )}
          />
        </TagsOutfield>

        <SearchButton variant="contained" endIcon={<SendIcon />}>
          Search
        </SearchButton>
      </Stack>
    </div>
  );
};
