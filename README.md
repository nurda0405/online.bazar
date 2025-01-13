This is **MVP** for my startup called **Online.bazar**. 

The idea of the startup was to **digitalize local markets in Astana**. 

For this I used **Telegram bot** in which the sellers could added clothes and clients see them.

**The logic of the system is as follows:**
1. Admin registers a seller to the bot;
2. The seller chooses category and sends image and description of the clothing;
3. Description and an image are stored in the database;
4. Client starts the bot and chooses the category of the clothing;
5. The image along with description will be sent to the client;
6. Client can go to the next clothing or can connect with the seller by the link to the seller that was sent as a button.

There were **3 bots** used in this system: bot for sellers, bot for clients and bot for admin. 

The source code of these bots you can find in the 'telegram' folder (they are called 'client_side.py', 'seller_side.py' and admin_side.py')

**Technical part:** 

For storing the information about the clothes was used **Django**. 

The tables you can find in models.py file in 'telegram' folder. Images are stored in 'images' folder. 

For running Telegram bots virtual server from '**Hoster.kz**' was bought.

**Promotion:** 

We went to the local market and registered **8 sellers** who added **12 clothes** to the bot. 

We opened Instagram account for the bot and run **paid ads** to get clients. 

In total **21 clients** have used our bot. 
![image](https://github.com/user-attachments/assets/b41bb9ae-82d0-47f9-b9fa-7fba38d51f65)
![image](https://github.com/user-attachments/assets/886c44b2-0336-42b0-b05d-5069ba09e3ce)



**Screenshots** from the bots: 
![image](https://github.com/user-attachments/assets/6d3095e7-ea47-4ac9-b0f4-c8fc95da0c22)
![image](https://github.com/user-attachments/assets/98bcd634-39c2-4ccb-9c77-3b5cc8c32e3c)
![image](https://github.com/user-attachments/assets/14d9b66a-ec37-47cb-9fed-a30f1870c1e3)
![image](https://github.com/user-attachments/assets/602b7afb-0944-4e36-be07-098956ed55cb)






