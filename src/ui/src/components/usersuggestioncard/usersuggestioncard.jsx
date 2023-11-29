import * as React from 'react';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { EndQuoteImg } from '../../assets';
import {
  QuoteImage,
  SuggestionCardContainer,
  CardMainContainer,
} from './elements';

function trimAndAppendDots(quote) {
  if (quote) {
    const maxLength = 110;

    if (quote.length > maxLength) {
      return quote.substring(0, maxLength - 3) + '...';
    } else {
      return quote;
    }
  }
}

export const UserSuggestionCard = ({ quote, author }) => {
  return (
    <CardMainContainer>
      <SuggestionCardContainer>
        <CardContent>
          <QuoteImage src={EndQuoteImg} component="img" />

          <Typography variant="h6" component="div" sx={{ color: '#FFF' }}>
            {trimAndAppendDots(quote) || 'no quote found'}
          </Typography>
          <Typography sx={{ color: '#bcb2b2', mb: 1.5 }}>
            ~{author || 'no author found'}
          </Typography>
        </CardContent>
        <CardActions sx={{ alignSelf: 'flex-end' }}>
          <Button size="small">Learn More</Button>
        </CardActions>
      </SuggestionCardContainer>
    </CardMainContainer>
  );
};
