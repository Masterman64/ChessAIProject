# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 14:20:29 2023

@author: jones

Chess pieces by Cburnett - Own work, CC BY-SA 3.0, https://commons.wikimedia.org/w/index.php?curid=1499803
"""

import os
import chess
import random
import cairosvg
import copy
import math
from functools import total_ordering
import PySimpleGUI as gui

@total_ordering
class TreeNode:
    iterations = 0
    
    def __init__(self, color, move, position, evaluation):
        self.color = color
        self.move = move
        self.position = position
        self.evaluation = evaluation
        self.parentNode = None
        self.childNodes = []
    
    def __eq__(self, other):
        if isinstance(other, TreeNode):
            return self.evaluation == other.evaluation and self.position == other.position
        else:
            return self.evaluation == other
        
    def __lt__(self, other):
        
        if isinstance(other, TreeNode):
            return self.evaluation < other.evaluation
        else:
            return self.evaluation < other
    
    def __hash__(self):
        return hash(("color", self.color, "position", self.position, 
                     "move", self.move, "evaluation", self.evaluation, "parentNode", 
                     self.parentNode, "childNodes", self.childNodes))
    
def evaluate(FENPosition):
    global checkerCount
    
    board = chess.Board(FENPosition)
    pieceMap = board.piece_map()
    
    if not board.turn: 
        opponentLegalMoves = list(board.copy().legal_moves)
        board.push(chess.Move.null())
        legalMoves = list(board.copy().legal_moves)
        board.push(chess.Move.null())
    else:
        legalMoves = list(board.copy().legal_moves)
        board.push(chess.Move.null())
        opponentLegalMoves = list(board.copy().legal_moves)
        board.push(chess.Move.null())
        
    pawnList = []
    opponentPawnList = []
    
    for c in range(checkerCount):
        pawnList.append([])
        opponentPawnList.append([])
     
    evaluation = 200 * (len(board.pieces(6, True)) - len(board.pieces(6, False)))
    evaluation += len(board.pieces(1, True)) - len(board.pieces(1, False))
    evaluation += 3 * (len(board.pieces(2, True)) - len(board.pieces(2, False)))
    evaluation += 3.5 * (len(board.pieces(3, True)) - len(board.pieces(3, False)))
    evaluation += 5 * (len(board.pieces(4, True)) - len(board.pieces(4, False)))
    evaluation += 9 * (len(board.pieces(5, True)) - len(board.pieces(5, False)))
    
    for p in pieceMap:
        if pieceMap[p].piece_type == 1:
            if pieceMap[p].color:
                pawnList[p % checkerCount].append(p)
            else:
                opponentPawnList[p % checkerCount].append(p)
            
    for rank in pawnList:
        index = pawnList.index(rank)
        
        if len(rank) > 0:
            # Checks for doubled pawns
            if len(rank) > 1:
                evaluation -= 0.5
            
            # Checks for isolated pawns
            if 0 < index + 1 < checkerCount and len(pawnList[index - 1]) == 0 and len(pawnList[index + 1]) == 0:
                evaluation -= 0.5
            
            # Checks for blocked pawns
            if board.piece_at(rank[-1] + (checkerCount)) != None:
                evaluation -= 0.5
            
    for rank in opponentPawnList:
        index = opponentPawnList.index(rank)
        
        if len(rank) > 0:
            # Checks for doubled pawns
            if len(rank) > 1:
                evaluation += 0.5
            
            # Checks for isolated pawns
            if 0 < index + 1 < checkerCount and len(opponentPawnList[index - 1]) == 0 and len(opponentPawnList[index + 1]) == 0:
                evaluation += 0.5
            
            if board.piece_at(rank[-1] - checkerCount) != None:
                evaluation += 0.5
    
    attacks = 0
    opponentAttacks = 0
    
    for move in legalMoves:
        if board.is_capture(move) > 0:
            attacks += 1
            
    for opponentMove in opponentLegalMoves:
        if board.is_capture(opponentMove):
            opponentAttacks += 1
    
    
    evaluation += 0.5 * (attacks - opponentAttacks)
    evaluation += 0.1 * (len(legalMoves) - len(opponentLegalMoves))
       
    return evaluation

def collectChildren(baseNode):
    turnBoard = chess.Board(baseNode.position)
    baseNode.childNodes = []
    
    for m in list(turnBoard.legal_moves):
        turnBoard.push(m)
        newNode = TreeNode(not copy.copy(turnBoard.turn), m.uci(), turnBoard.fen(), evaluate(turnBoard.fen()))
        
        if ((not newNode.color) and newNode.evaluation > baseNode.evaluation - 4) or (newNode.color and newNode.evaluation < baseNode.evaluation + 4):
            baseNode.childNodes.append(newNode)
            
        turnBoard.pop()
        
    for c in baseNode.childNodes:
        c.parentNode = baseNode

def alphaBetaMax(currentNode, depthLeft, alpha = -math.inf, beta = math.inf):
    
    if depthLeft == 0:
        return currentNode
   
    currentNode.childNodes.sort(reverse = True)
    
    for n in currentNode.childNodes:
        TreeNode.iterations += 1
            
        collectChildren(n)
        score = alphaBetaMin(n, depthLeft - 1, alpha, beta)
        
        if score >= beta:
            n.evaluation = score.evaluation
            return n
           
        if score > alpha:
            n.evaluation = score.evaluation
            alpha = n
   
    return alpha

def alphaBetaMin(currentNode, depthLeft, alpha = -math.inf, beta = math.inf):
    if depthLeft == 0 or len(currentNode.childNodes) == 0:
        return currentNode
    
    currentNode.childNodes.sort()
    
    for n in currentNode.childNodes:
        TreeNode.iterations += 1
        
        collectChildren(n)
        score = alphaBetaMax(n, depthLeft - 1, alpha, beta)
        
        if score <= alpha:
            n.evaluation = score.evaluation
            return n
       
        if score < beta:
            n.evaluation = score.evaluation
            beta = n
           
    return beta

def alphaBetaSearch(depth):
    global board, startingPlayer
    
    TreeNode.iterations = 0
    baseNode = TreeNode(not board.turn, board.peek().uci(), board.fen(), evaluate(board.fen()))
    
    collectChildren(baseNode)
    
    if startingPlayer == "Human":
        deepestNode = alphaBetaMin(baseNode, depth, baseNode)
    else:
        deepestNode = alphaBetaMax(baseNode, depth, beta = baseNode)

    print(deepestNode.evaluation)
    print(TreeNode.iterations)
    
    return board.parse_uci(deepestNode.move)

def drawMarkers(pieceSquare):
    global spaceSize, startingPlayer, flipIfAI, board, moveMarkers
    
    if len(moveMarkers) != 0:
        for marker in moveMarkers:
            graph.DeleteFigure(marker)
        moveMarkers = []
    
    for move in list(filter(lambda m: m.from_square == pieceSquare, board.legal_moves)):
        movePos = ( 
            ((move.to_square % checkerCount) * spaceSize + (spaceSize - 1 if startingPlayer == "AI" else 1)) * flipIfAI,
            ((move.to_square // checkerCount) * spaceSize + (spaceSize if startingPlayer == "Human" else 0)) * flipIfAI
        )
        
        rowOffset = (move.to_square // checkerCount) % 2 
        
        image = os.path.join(relativePath, "images\\moveMarker" + ("Alt" if (move.to_square + rowOffset) % 2 == 0 else "") + ".svg" )
        
        moveMarkers.append(graph.draw_image(data = cairosvg.svg2png(url = image, parent_width = spaceSize,
                        parent_height = spaceSize), location = movePos))
        
def drawPiece(piece, position):
    global relativePath, spaceSize, graph
        
    image = os.path.join(relativePath, "images\\" + parsePiece(piece) + ".svg")
    
    return graph.draw_image(data = cairosvg.svg2png(url = image, parent_width = spaceSize,
                    parent_height = spaceSize), location = position)

def drawPieceMove(piece, xOffset = 0, yOffset = 0):
    global flipIfAI, graph
    
    graph.move_figure(piece, xOffset, yOffset)
    
def drawCastle(move):
    global checkerCount, spaceSize, board, startingPlayer
    
    piece = None
    isWhite = board.piece_at(move.from_square).color
    isKingside = board.is_kingside_castling(move)
    isKingMoving = "King" in parsePiece(board.piece_at(move.from_square))
    
    kingPos = ( 
        5 * spaceSize * flipIfAI,
        (0 if isWhite and startingPlayer == "Human" else checkerCount) * spaceSize * flipIfAI
    )
    
    rookPos = ( 
        (checkerCount if isKingside else 1) * spaceSize * flipIfAI,
        (0 if isWhite and startingPlayer == "Human" else checkerCount) * spaceSize * flipIfAI
    )
    
    if isKingMoving:
        piece = graph.GetFiguresAtLocation((rookPos[0], rookPos[1]))[-1]
        drawPieceMove(piece, spaceSize * (3 if not isKingside else -2))
    else:
        piece = graph.GetFiguresAtLocation((kingPos[0], kingPos[1]))[-1]
        drawPieceMove(piece, spaceSize * (2 if not isKingside else -2))
            
def parsePiece(piece):
    pieceName = "white" if piece.color else "black"
    
    if piece.piece_type == 1:
        pieceName += "Pawn"
    elif piece.piece_type == 2:
        pieceName += "Knight"
    elif piece.piece_type == 3:
        pieceName += "Bishop"
    elif piece.piece_type == 4:
        pieceName += "Rook"
    elif piece.piece_type == 5:
        pieceName += "Queen"
    elif piece.piece_type == 6:
        pieceName += "King"
        
    return pieceName

def parsePieceType(pieceName):
    if pieceName.lower() == "pawn":
        return 1
    elif pieceName.lower() == "knight":
        return 2
    elif pieceName.lower() == "bishop":
        return 3
    elif pieceName.lower() == "rook":
        return 4
    elif pieceName.lower() == "queen":
        return 5
    elif pieceName.lower() == "king":
        return 6
    
def init():
    global relativePath, boardSize, spaceSize, checkerCount, startingPlayer, flipIfAI, startingMoves, moveMarkers, moveStack
    
    relativePath = os.path.dirname(os.path.abspath(__file__))
    
    boardSize = 320
    checkerCount = 8
    spaceSize = boardSize / checkerCount
    startingPlayer = "Human"
    
    
    startingMoves = [chess.Move(chess.E2, chess.E4), chess.Move(chess.C2, chess.C4),
                     chess.Move(chess.D2, chess.D3), chess.Move(chess.G1, chess.F3)]
    moveMarkers = []
    moveStack = []
    
    setLayout()
    setBoard(chess.Board())

def setLayout():
    global boardSize, startingPlayer, flipIfAI, window, graph, table
    
    flipIfAI = 1 if startingPlayer == "Human" else -1
    
    layout = [
        [gui.Text("Chess")],
        [gui.Graph((boardSize, boardSize), 
                   (0 if startingPlayer == "Human" else -boardSize, 0 if startingPlayer == "Human" else -boardSize), 
                   (boardSize if startingPlayer == "Human" else 0, boardSize if startingPlayer == "Human" else 0), 
                   key='-GRAPH-', change_submits=True, drag_submits=True), 
         gui.Table(moveStack, ["Turn", "White", "Black"], justification = "center", 
                   key = "-TABLE-")],
        [gui.Button("Reset", key="Reset"), 
         gui.Button("Start As White", key = "White", visible = startingPlayer == "AI"), 
         gui.Button("Start As Black", key = "Black", visible = startingPlayer == "Human"), 
         gui.Button("Load Game", key = "Load"), gui.Button("Export Game", key = "Export")]
    ]
    
    window = gui.Window('Chess', layout, transparent_color="grey50", finalize=True)
    graph = window['-GRAPH-']
    table = window["-TABLE-"]
    
def setBoard(newBoard):
    global spaceSize, boardSize, checkerCount, startingPlayer, flipIfAI, board, pieceMap, window, graph
    
    board = newBoard
    
    pieceMap = board.piece_map()
    
    graph.Erase()
    
    counter = 0
    
    for row in range(checkerCount):
        for col in range(checkerCount):
            
            if col == 1:
                graph.SendFigureToBack(graph.draw_text('{}'.format(str(col + 1)),  
                    (col * spaceSize, row * spaceSize),
                    font = "Default 5"))
            if row == 8:
                graph.SendFigureToBack(graph.draw_text('{}'.format(chr(col + 97)),  
                    ((col * spaceSize - 5), (row * spaceSize - 5)),
                    font = "Default 5"))
            
            graph.SendFigureToBack(graph.draw_rectangle(
                 (col * spaceSize * flipIfAI, row * spaceSize * flipIfAI), 
                 ((col * spaceSize + spaceSize) * flipIfAI, (row * spaceSize + spaceSize) * flipIfAI), 
                 line_color = 'black',
                 fill_color='tan4' if (counter + row % 2) % 2 == 0 else 'burlywood2'))
            
            if counter in pieceMap:
                if startingPlayer == "Human":
                    drawPiece(pieceMap.get(counter), (col * spaceSize - 1, 
                        (row + 1) * spaceSize + 3))
                else:
                    drawPiece(pieceMap.get(counter), (col * -spaceSize - 1 - spaceSize, 
                        (row + 1) * -spaceSize + 3 + spaceSize))
            
            counter += 1
def mainLoop():
    global spaceSize, checkerCount, startingPlayer, startingMoves, board, pieceMap, turn, move, moveMarkers, moveStack, window, graph, table
    
    fromSquare = None
    movingPiece = None
    oldPos = None
    defaultDepth = 1
    depth = None
    
    while not isinstance(depth, int):
        depth = gui.popup_get_text("Please enter how deep you want the AI to go.",
                               "Choose AI Depth", str(defaultDepth))
        depth = int(depth) if isinstance(depth, str) and depth.isdigit() and int(depth) >= 0 else None
        
    while not board.is_game_over():
        event, values = window.read()
        print(event, values)
        if event in (gui.WIN_CLOSED, 'Exit'):
            break
        mouse = values['-GRAPH-']
        
    
        if event == '-GRAPH-':
            if mouse == (None, None):
                continue
            
            if startingPlayer == "Human":
                box_x = mouse[0]//spaceSize
                box_y = mouse[1]//spaceSize
            else:    
                box_x = mouse[0]//spaceSize * flipIfAI - 1
                box_y = mouse[1]//spaceSize * flipIfAI - 1
            
            inXRange = 0 <= box_x < checkerCount
            inYRange = 0 <= box_y < checkerCount
            
            clickedSquare = int(chess.square(box_x, box_y)) 
            
            if inXRange and inYRange:
                figuresAtLocation = graph.GetFiguresAtLocation((mouse[0], mouse[1]))
                pieceAtClickedSquare = board.piece_at(clickedSquare)
                
                if fromSquare != None or pieceAtClickedSquare != None:
                    if fromSquare != None and pieceAtClickedSquare == None or fromSquare != None and pieceAtClickedSquare != None and pieceAtClickedSquare.color != board.turn:
                        isLegalMove = board.legal_moves.__contains__(chess.Move(fromSquare, clickedSquare))
                        isPromotion = board.piece_at(chess.Move(fromSquare, clickedSquare).from_square) != None and board.piece_at(chess.Move(fromSquare, clickedSquare).from_square).piece_type == 1 and (box_y == 1 or box_y == 7)
                        
                        if isLegalMove or isPromotion:
                            move = chess.Move(fromSquare, clickedSquare)
                            newPos = [box_x * spaceSize * flipIfAI, box_y * spaceSize * flipIfAI]
                            isMoveCancelled = False    
                            
                            if board.piece_at(move.from_square).piece_type == 1 and (box_y == 1 or box_y == 7):
                                pieceType = gui.popup_get_text("What piece would you like to promote to?\nYou may choose from Knight, Bishop, Rook, and Queen.",
                                                   title = "Promotion", default_text = "Queen",
                                                   keep_on_top = True)
                                
                                if pieceType != None:
                                    move.promotion = pieceType
                                else:
                                    isMoveCancelled = True
                                    
                            if not isMoveCancelled:
                                for marker in moveMarkers:
                                    graph.DeleteFigure(marker)
                                    
                                moveMarkers = []
                                
                                if move.promotion != None:
                                    promotedPiece = chess.Piece(move.promotion, board.turn)
                                    
                                    graph.DeleteFigure(movingPiece)
                                    
                                    movingPiece = drawPiece(promotedPiece, (newPos[0] + spaceSize - 1, newPos[1] + 3))
                                
                                if board.is_castling(move):
                                    drawCastle(move)
                                elif board.is_en_passant(move):
                                    figuresAtLocation = graph.GetFiguresAtLocation((newPos[0] + spaceSize / 2 * flipIfAI, newPos[1] - (spaceSize / 2 if startingPlayer == "Human" else spaceSize * 1.5)))
                                    
                                    for figure in figuresAtLocation:
                                        if figure != figuresAtLocation[0] and figure != movingPiece:
                                            graph.DeleteFigure(figure)
                                elif not board.piece_at(clickedSquare) == None:
                                    for figure in figuresAtLocation:
                                        if figure != figuresAtLocation[0] and figure != movingPiece:
                                            graph.DeleteFigure(figure)
                                
                                drawPieceMove(movingPiece, newPos[0] - oldPos[0], newPos[1] - oldPos[1])
                                    
                                board.push(move)
                                
                                pieceMap = board.piece_map()
                                
                                if not board.is_game_over():
                                    opponentMove = alphaBetaSearch(depth)
                                    
                                    xOffset = (opponentMove.to_square % checkerCount - opponentMove.from_square % checkerCount) * spaceSize * flipIfAI
                                    
                                    yOffset = ((opponentMove.to_square // checkerCount - opponentMove.from_square // checkerCount)) * spaceSize * flipIfAI
                                    
                                    oldPos = ( 
                                        (opponentMove.from_square % checkerCount) * spaceSize * flipIfAI,
                                        ((opponentMove.from_square // checkerCount)) * spaceSize * flipIfAI
                                    )
                                    
                                    opponentFromMoveLocation = graph.GetFiguresAtLocation(
                                        (oldPos[0] + (spaceSize / 2) * flipIfAI,
                                         oldPos[1] + (spaceSize / 2) * flipIfAI) 
                                    )
                                    
                                    opponentToMoveLocation = graph.GetFiguresAtLocation(
                                        (oldPos[0] + xOffset + (spaceSize / 2) * flipIfAI,
                                         oldPos[1] + yOffset + (spaceSize / 2) * flipIfAI) 
                                    )
                                    
                                    if board.is_castling(opponentMove):
                                        drawCastle(opponentMove)
                                    elif board.is_en_passant(move):
                                        figuresAtLocation = graph.GetFiguresAtLocation((newPos[0] + spaceSize / 2 * flipIfAI, newPos[1] + (spaceSize / 2 if startingPlayer == "Human" else spaceSize * 1.5)))
                                        
                                        for figure in figuresAtLocation:
                                            if figure != figuresAtLocation[0] and figure != movingPiece:
                                                graph.DeleteFigure(figure)
                                    elif not board.piece_at(opponentMove.to_square) == None:
                                        for figure in opponentToMoveLocation:
                                            if figure != opponentToMoveLocation[0] and figure != opponentFromMoveLocation[-1]:
                                                graph.DeleteFigure(figure)
                                    
                                    if opponentMove.promotion != None:
                                        promotedPiece = chess.Piece(opponentMove.promotion, board.turn)
                                        
                                        graph.DeleteFigure(opponentFromMoveLocation)
                                        drawPiece(promotedPiece, (oldPos[0] + xOffset, oldPos[1] + yOffset))
                                    else:
                                        drawPieceMove(opponentFromMoveLocation[-1], xOffset, yOffset)
                                    
                                    board.push(opponentMove)
                                    
                                    moveStack.append([len(board.move_stack) // 2, move, opponentMove])
                                    table.update(moveStack)
                                    table.set_vscroll_position(1)
                        else:
                            for marker in moveMarkers:
                                graph.DeleteFigure(marker)
                                
                            moveMarkers = []
                            
                            fromSquare = None
                    else:
                        oldPos = (box_x * spaceSize * flipIfAI, 
                                  box_y * spaceSize * flipIfAI)
                        fromSquare = clickedSquare
                        movingPiece = figuresAtLocation[-1]
                        
                        drawMarkers(clickedSquare)
                else:
                    for marker in moveMarkers:
                        graph.DeleteFigure(marker)
                        
                    moveMarkers = []
                    
                    fromSquare = None
                    
        if board.is_game_over() or event == "Reset" or event == "White" or event == "Black":
            if board.is_checkmate():
                gui.popup_ok("Checkmate!\n{} wins the game!".format("White" if not board.turn else "Black"))
            elif board.is_fivefold_repetition():
                gui.popup_ok("It's a draw!\nThe same position has happened 5 times in a row, forcing a draw!")
            elif board.is_insufficient_material():
                gui.popup_ok("It's a draw!\nNeither side has enough material to win, forcing a draw!")
            elif board.is_seventyfive_moves():
                gui.popup_ok("It's a draw!\nIt has been 75 turns since a capture or pawn move has taken place, forcing a draw!")
            elif board.is_stalemate():
                gui.popup_ok("It's a draw!\n{} has no more legal moves, resulting in a stalemate!".format("White" if board.turn else "Black"))
            
            
            newBoard = chess.Board()
            if event == "Black" or (startingPlayer == "AI" and (event == "Reset" or board.is_game_over())):
                newBoard.push(random.choice(startingMoves))
                startingPlayer = "AI"
                
            else:
                startingPlayer = "Human"
                
            moveStack = []
                
            table.update(moveStack)
            window.close()
            setLayout()
            setBoard(newBoard)
        
            fromSquare = None
            movingPiece = None
            oldPos = None
            depth = None
            
            while not isinstance(depth, int):
                depth = gui.popup_get_text("Please enter how deep you want the AI to go.",
                                       "Choose AI Depth", str(defaultDepth))
                depth = int(depth) if isinstance(depth, str) and depth.isdigit() and int(depth) >= 0 else None
        
            
        if event == "Load":
            newBoard = chess.Board(gui.popup_get_text("Please enter a chess position matching the FEN standard.", "Load Game"))
            
            if newBoard != None:
                startingPlayer = "Human" if newBoard.turn else "AI"
                
                moveStack = []
                table.update(moveStack)
                window.close()
                
                setLayout()
                setBoard(newBoard)
            
        if event == "Export":
            gui.clipboard_set(board.fen())
            gui.popup("The position has been copied to the clipboard in the FEN standard!")
        if event == gui.WINDOW_CLOSED:
            break    
                  
init()        
mainLoop()
window.close()