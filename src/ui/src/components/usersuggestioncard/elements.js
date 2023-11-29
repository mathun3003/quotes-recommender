import { styled, Box, Card } from '@mui/material';

export const QuoteImage = styled(Box)({
  width: '80px',
  height: '80px',
});

export const CardMainContainer = styled(Box)({
  minWidth: 225,
  padding: '10px',
});

export const SuggestionCardContainer = styled(Card)({
  minHeight: 300,
  background:
    'linear-gradient(90deg, #092626 0.24%, rgba(46, 44, 44, 0.66) 49.62%, rgba(132, 68, 154, 0.28) 105.83%, rgba(0, 0, 0, 0.11) 146.1%)',
});
