import Slider from 'react-slick';
// import { UserSuggestionCard } from './elements';
import { Box } from '@mui/material';
import { UserSuggestionCard } from '../usersuggestioncard';
import { sampleQuotes } from './quotes';

export const UserSuggestions = () => {
  const settings = {
    dots: true,
    infinite: true,
    speed: 500,
    slidesToShow: 3,
    slidesToScroll: 3,
    centerPadding: '50px',
  };

  return (
    <Box sx={{ padding: '10px 50px' }}>
      <h2> Other users also liked/looked for </h2>

      {sampleQuotes?.length > 0 && (
        <Slider {...settings}>
          {sampleQuotes.map((item) => (
            <UserSuggestionCard quote={item?.quote} author={item?.author} />
          ))}
        </Slider>
      )}
    </Box>
  );
};
