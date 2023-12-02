import React, { useState } from 'react';
import './searchbox.css';
import {
  SearchField,
  TagsField,
  SearchButton,
  PaperComponentContainer,
  TagsOutfield,x
} from './elements';
import InputAdornment from '@mui/material/InputAdornment';
import Autocomplete from '@mui/material/Autocomplete';
import SearchIcon from '@mui/icons-material/Search';
import SendIcon from '@mui/icons-material/Send';
import Stack from '@mui/material/Stack';

import{
  ResultsContainer,
  Header,
  ChatBubbleContainer,
  ChatBubble,
  Bubble,
  BubbleContainer,
} from '../results/elements';

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

const mockResponseData = {
  message: "success",
  limit: 10,
  count: 10,
  data: [
    {
      id: 1,
      text: "Be yourself; everyone else is already taken.",
      author: "Oscar Wilde",
      tags: ["be-yourself", "inspirational"],
    },
    {
      id: 2,
      text: "Be yourself; everyone else is already taken.",
      author: "Oscar Wilde",
      tags: ["be-yourself", "inspirational"],
    },
  ],
  filters: ["inspirational"],
  query: "be yourself"
};

export const SearchBox = () => {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [responseData, setResponseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const limit = 10; // Dies können Sie als konstanten Wert behalten oder als State definieren, wenn es variabel sein soll

  const handleSearch = async () => {
    setIsLoading(true);
    // Verzögern Sie die Ausführung, um das Verhalten einer Netzwerkanfrage zu simulieren
    setTimeout(() => {
      setResponseData(mockResponseData); // Verwenden Sie die Mock-Daten
      setIsLoading(false);
    }, 1000); // Verzögerung von 1000 Millisekunden (1 Sekunde)
  };

  // Ereignis-Handler für die Suche
 // const handleSearch = async () => {
 //   setIsLoading(true);
 //   try {
      // Erstellen Sie hier Ihren requestBody mit den aktuellen Zuständen für query und selectedTags
  //    const requestBody = {
  //      query,
  //      filters: selectedTags.map(tag => tag.value),
  //      limit: 10,
  //      collection: '', // Setzen oder entfernen Sie diese Eigenschaft je nach Bedarf
  //    };

   //   const response = await fetch('YOUR_BACKEND_ENDPOINT', {
  //      method: 'POST',
  //      headers: {
  //        'Content-Type': 'application/json',
  //      },
  //      body: JSON.stringify(requestBody),
   //   });

  //    if (!response.ok) {
   //     throw new Error(`HTTP error! status: ${response.status}`);
  //    }

  //    const data = await response.json();
  //    setResponseData(data);
  //  } catch (error) {
  //    console.error('There was an error!', error);
  //  }
  //  setIsLoading(false);
  //};
  return (
    <div className="search-box">
      <Stack spacing={2} alignItems="center">
        <h1 className="search-title">What are you looking for ?</h1>
  
        <SearchField
          placeholder="Search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
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
            onChange={(event, newValue) => {
              setSelectedTags(newValue);
            }}
            PaperComponent={PaperComponentContainer}
            renderInput={(params) => (
              <TagsField {...params} placeholder="Tags" />
            )}
          />
        </TagsOutfield>
  
        <SearchButton variant="contained" endIcon={<SendIcon />} onClick={handleSearch}>
          Search
        </SearchButton>
      </Stack>
      {isLoading && <p>Loading...</p>}
      {!isLoading && responseData && (
        <>    
            <Header>Results</Header>
            <BubbleContainer>
              {responseData.data.map((quote, index) => (
                <ChatBubble
                  key={quote.id}
                  text={quote.text}
                  author={quote.author}
                  tags={quote.tags}
                  position={index % 2 === 0 ? 'left' : 'right'}
                />
              ))}
            </BubbleContainer>      
        </>
      )}
    </div>
  );
};