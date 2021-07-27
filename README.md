# DatePoll

A Discord bot that keeps track of when members say they're available for the next thing.

## Working Features

## Planned Features

* keep an updated dictionary of dates when members are available
    * store permanently with the pickle package
    * delete past dates
* provide text commands for users
    * handle date ranges
    * need to be able to remove dates
    * sanitize inputs, raise Errors, make safe, make clear
* display dates in text
* display dates embedded
* post polls for users to fill out
    * see if we can avoid using reactions, or if we can override the numbering on reactions
* allow users to define 'critical mass'. That is, if a specified number of people are available on the same date, have
  the bot @ whoever defined the critical mass
* allow input of time of day information
* Google Calendar webhooks
    * commands to make Google Calendar Events
        * with specified date and time
        * with soonest mutually available date and time
        * to tell the bot to do this automatically
* let users explain their level of availability
