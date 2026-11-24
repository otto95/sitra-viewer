# Vietnam Conflict Data Explorer Project

## Business Requirements

- An MVP of an application for exploring data held by National Archives about the Vietnam conflict as a web app
- The data for the MVP is the "Records About the Ground Combat Operations by the Army During the Vietnam War, 5/20/1966 - 3/12/1973 also known as Situation Report Army" available from NARA (https://catalog.archives.gov/id/604416). 
- The web app should allow searching the data based and filter by time limit. 
- The web app should plot search results on a map.
- The web app should plot search results on a timeline according to when they were created.
- The web app should be able to show a network graph of an individual record and the records associated to it. 
- No more functionality: Keep it simple.
- The priority is a slick, professional, gorgeous UI/UX with very simple features

## Technical Details

- Implemented as a modern React app, client rendered with a python backend
- Use a graph database for persistent storage of historical data. Meta data or user data can be stored in a relational database
- The React app should be created in a subdirectory `frontend`
- MVP should be able to be deployed with containers
- No user management for the MVP
- Use popular libraries
- Use open-source no cost lisencing
- As simple as possible but with an elegant UI

## Development Process
- Read the plan
- Implement the plan
- Make a git commit and a pull request

## Color Scheme

- Olive Drab: `#556B2F` - accent lines, highlights
- Field Green: `#3F5940` - links, key sections
- Coyote Tan: `#B58B5A` - submit buttons, important actions
- Deep Charcoal: `#242820` - main headings
- Warm Gray: `#77766D` - supporting text, labels
- Parchment: `#F3F0E6` - page and record backgrounds

## Strategy

1. Write plan with success criteria for each phase to be checked off. Include project scaffolding, including .gitignore, and rigorous unit testing.
2. Execute the plan ensuring all critiera are met
3. Carry out extensive integration testing with Playwright or similar, fixing defects
4. Only complete when the MVP is finished and tested, with the server running and ready for the user

## Coding standards

1. Use latest versions of libraries and idiomatic approaches as of today
2. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.
3. Be concise. Keep README minimal. IMPORTANT: no emojis ever
