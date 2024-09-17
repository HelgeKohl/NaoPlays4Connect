using OpenCvSharp;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

public class NaoSocketServer : MonoBehaviour
{
    System.Threading.Thread SocketThread;
    volatile bool keepReading = false;
    internal static byte[] ImageBytes = null;
    public static WinState WinState { get; private set; }
    public static int SuggestedIndex { get; private set; }
    public static bool NaoRequestActive { get; internal set; }
    public static bool NaoRequestFinished { get; internal set; }
    public static int BufferSize { get; internal set;  } = 65536;
    public static string PythonNaoPath { 
        get
        {
            return Path.Combine(Directory.GetParent(Directory.GetCurrentDirectory()).FullName, "python-nao");
        }
    }

    public static Texture2D CurrentTexture2D { get; internal set; }


    // Use this for initialization
    void Start()
    {
        Debug.Log("Start NaoSocketServer");
        Application.runInBackground = true;
        startServer();
    }

    void startServer()
    {
        SocketThread = new System.Threading.Thread(networkCode);
        SocketThread.IsBackground = true;
        SocketThread.Start();
    }



    private string getIPAddress()
    {
        IPHostEntry host;
        string localIP = "";
        host = Dns.GetHostEntry(Dns.GetHostName());
        foreach (IPAddress ip in host.AddressList)
        {
            if (ip.AddressFamily == AddressFamily.InterNetwork)
            {
                localIP = ip.ToString();
            }

        }
        return localIP;
    }


    Socket listener;
    Socket handler;



    public static void AppendAllBytes(string path, byte[] bytes)
    {
        //argument-checking here.

        using (var stream = new FileStream(path, FileMode.Append))
        {
            stream.Write(bytes, 0, bytes.Length);
        }
    }
    void networkCode()
    {
        string data;

        // Data buffer for incoming data.
        byte[] bytes = new Byte[BufferSize];

        // host running the application.
        Debug.Log("Ip " + getIPAddress().ToString());
        IPAddress[] ipArray = Dns.GetHostAddresses(getIPAddress());
        IPEndPoint localEndPoint = new IPEndPoint(ipArray[0], 9001);

        // Create a TCP/IP socket.
        listener = new Socket(ipArray[0].AddressFamily,
            SocketType.Stream, ProtocolType.Tcp);

        // Bind the socket to the local endpoint and 
        // listen for incoming connections.
        try
        {
            listener.Bind(localEndPoint);
            listener.Listen(10);

            // Start listening for connections.
            while (true)
            {
                keepReading = true;

                // Program is suspended while waiting for an incoming connection.
                Debug.Log("Waiting for Connection");
                handler = listener.Accept();
                Debug.Log("Client Connected");
                data = null;

                // An incoming connection needs to be processed.
                while (keepReading)
                {
                    byte[] content = GetFileContent(handler);
                    keepReading = false;

                    AppendAllBytes(Path.Combine(PythonNaoPath, "tmp", "unity.png"), content);


                    string file = Path.Combine(PythonNaoPath, "tmp", "unity.png");
                    string file_current = Path.Combine(PythonNaoPath, "tmp", "unity_current.png");

                    // Delete old unity_current.png file, if it exists
                    if (File.Exists(file_current))
                    {
                        File.Delete(file_current);
                    }
                    File.Move(file, file_current);
                    // Delete tmp unity.png file
                    if (File.Exists(file))
                    {
                        File.Delete(file);
                    }

                    NaoSocketServer.ImageBytes = File.ReadAllBytes(file_current);

                    // Zurücksetzen
                    NaoSocketServer.CurrentTexture2D = null;

                    NaoSocketServer.NaoRequestActive = true;
                    NaoSocketServer.NaoRequestFinished = false;

                    Debug.Log("Request Active");

                    while (NaoSocketServer.NaoRequestActive)
                    {
                        System.Threading.Thread.Sleep(100);
                    }


                    data = null;

                    object[] items = new object[2];
                    items[0] = (int) NaoSocketServer.WinState;
                    items[1] = NaoSocketServer.SuggestedIndex;
                    byte[] packed = StructConverter.Pack(items);

                    handler.Send(packed);

                    if (WinState == WinState.Draw ||
                        WinState == WinState.RedWin ||
                        WinState == WinState.YellowWin ||
                        WinState == WinState.AmountOfHolesIsWrong ||
                        WinState == WinState.Wrong)
                    {
                        NaoSocketServer.SetState(WinState.MatchNotFinished, -1);
                    }
                    
                }

                System.Threading.Thread.Sleep(1);    
            }
        }
        catch (Exception e)
        {
            Debug.Log("NAO SOCKET ERROR - " + e.ToString());
        }
    }

    byte[] GetFileContent(Socket handler)
    {
        int packagesReceived = 0;
        int total = 0;
        int recv;
        byte[] datasize = new byte[4];

        recv = handler.Receive(datasize, 0, 4, SocketFlags.None);

        int size = BitConverter.ToInt32(datasize, 0);


        int dataleft = size;
        Debug.Log("Transmit File - Size: " + size + " Bytes");
        byte[] data = new byte[size];

        while (total < size)
        {
            recv = handler.Receive(data, total, dataleft, 0);
            packagesReceived += 1;

            if (recv == 0)
            {
                break;
            }
            total += recv;
            dataleft -= recv;

            Debug.Log("Transmitted: " + Math.Round((double)(total / size), 2) * 100 + " % (#" + +packagesReceived + ")");
        }

        Debug.Log("Data transmitted");

        return data;
    }

    void stopServer()
    {
        keepReading = false;

        //stop thread
        if (SocketThread != null)
        {
            SocketThread.Abort();
        }

        if (handler != null && handler.Connected)
        {
            handler.Disconnect(false);
            Debug.Log("Disconnected!");
        }
    }

    void OnDisable()
    {
        stopServer();
    }

    internal static void SetState(WinState winState, int suggestedIndex)
    {
        WinState = winState;
        SuggestedIndex = suggestedIndex;
        Debug.Log("Winstate: " + (int)WinState + " SuggestedIndex: " + suggestedIndex);
    }
}

