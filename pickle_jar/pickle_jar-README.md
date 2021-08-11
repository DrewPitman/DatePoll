# pickle_jar

Simply put, you can't add an empty directory to Git or GitHub. 
So I've added this file so that I can commit the directory.
The purpose of this directory is to hold all ".p" pickle files 
for the DatePollBot.

Pickle files save data structures for future use. That way, 
we can restart the bot without losing the dictionaries it 
had in memory.
The pickle files here are of the forms
>availability_[guild id].p <br>
> cm_[guild id].p

and they store information about member availability and critical mass.