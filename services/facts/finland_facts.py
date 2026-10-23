"""Ready-made questions and facts about Finland, grouped by topic.

Each entry is (question, fact). The orchestrator asks Gemma to answer the
question using only the fact, so keep facts short and self-contained.
Topic keys must match TOPICS in frontend/frontend.py.
"""

FINLAND_FACTS = {
    "lakes": [
        ("How many lakes does Finland have?",
         "Finland has 187,888 lakes larger than 500 square meters, which is why it is "
         "often called the land of a thousand lakes."),
        ("What is Finland's largest lake?",
         "Saimaa is Finland's largest lake and one of the largest lakes in Europe."),
        ("What rare animal lives in Lake Saimaa?",
         "The Saimaa ringed seal lives only in Lake Saimaa and is one of the world's most "
         "endangered seals, with only a few hundred left."),
    ],
    "saunas": [
        ("How many saunas are there in Finland?",
         "Finland has around three million saunas for a population of about 5.6 million people."),
        ("Is Finnish sauna culture recognized by UNESCO?",
         "Finnish sauna culture was added to UNESCO's list of Intangible Cultural Heritage in 2020."),
        ("Where does the word sauna come from?",
         "Sauna is a Finnish word and one of the few Finnish words adopted into English "
         "and many other languages."),
    ],
    "nature": [
        ("How much of Finland is covered by forest?",
         "About 75 percent of Finland's land area is covered by forest, making it the most "
         "forested country in Europe."),
        ("What are everyman's rights in Finland?",
         "Everyman's rights let anyone walk in nature and pick wild berries and mushrooms, "
         "even on land they don't own, as long as they cause no harm or disturbance."),
    ],
    "lapland": [
        ("Does the sun really not set in Finland?",
         "In northernmost Lapland the sun does not set for about two months in summer, "
         "a phenomenon called the midnight sun."),
        ("How often can you see the northern lights in Finland?",
         "In Finnish Lapland the northern lights can be seen on up to about 200 nights a year."),
        ("Where does Santa Claus live?",
         "Rovaniemi, the capital of Finnish Lapland, sits on the Arctic Circle and is promoted "
         "as the official hometown of Santa Claus."),
    ],
    "islands": [
        ("How many islands does Finland have?",
         "Finland has about 179,000 islands, counting those along the coast and in its lakes."),
        ("What is special about Åland?",
         "Åland is an autonomous, demilitarized and Swedish-speaking region of Finland made up "
         "of thousands of islands."),
    ],
    "history": [
        ("When did Finland become independent?",
         "Finland declared independence on 6 December 1917, and the date is celebrated "
         "as Independence Day."),
        ("Were Finnish women early to get the right to vote?",
         "In 1906 Finland became the first country in Europe to give women the right to vote, "
         "and the first in the world to let them stand for parliament."),
    ],
    "languages": [
        ("What are Finland's official languages?",
         "Finland has two official languages, Finnish and Swedish, and the Sámi languages "
         "have official status in the Sámi homeland in Lapland."),
        ("Which languages are related to Finnish?",
         "Finnish is a Uralic language, closely related to Estonian and distantly related "
         "to Hungarian, unlike most European languages."),
    ],
    "technology": [
        ("Which famous operating system started in Finland?",
         "Linus Torvalds started the Linux kernel in 1991 while he was a student at the "
         "University of Helsinki."),
        ("Who invented SSH?",
         "Tatu Ylönen created the SSH protocol in 1995 at the Helsinki University of Technology."),
        ("Where was IRC invented?",
         "Jarkko Oikarinen created Internet Relay Chat, IRC, in 1988 at the University of Oulu."),
    ],
    "culture": [
        ("Who created the Moomins?",
         "The Moomins were created by Finnish author and artist Tove Jansson, who published "
         "the first Moomin book in 1945."),
        ("Do Finns drink a lot of coffee?",
         "Finland has one of the highest per capita coffee consumption rates in the world."),
        ("What is the Wife Carrying World Championship?",
         "The Wife Carrying World Championships are held every summer in Sonkajärvi, Finland."),
    ],
}
