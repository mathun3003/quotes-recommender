import {
  ResultsContainer,
  Header,
  ChatBubbleContainer,
  Bubble,
  BubbleContainer,
} from './elements';
import { quotes } from './samplequotes';

const ChatBubble = ({ message, position }) => (
  <ChatBubbleContainer position={position}>
    <Bubble position={position}>{message}</Bubble>
  </ChatBubbleContainer>
);

export const Results = () => {
  return (
    <>
      <ResultsContainer>
        <Header>Results</Header>

        <BubbleContainer>
          {quotes.map((text, index) => (
            <ChatBubble
              message={text}
              position={index % 2 === 0 ? 'left' : 'right'}
            />
          ))}
        </BubbleContainer>
      </ResultsContainer>
    </>
  );
};
